package main

import (
	"archive/zip"
	"bytes"
	"errors"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"unicode/utf8"
)

const defaultSuffix = "_sanitizado"

var (
	fixedKeys   = []string{"raft_first_layer_expansion", "tree_support_wall_count"}
	keysPattern = "(?:" + strings.Join(fixedKeys, "|") + ")"
	patterns    = []struct {
		re          *regexp.Regexp
		replacement string
	}{
		// JSON: "clave": "-1" o "clave": -1. Los valores de configuración se guardan como string.
		{regexp.MustCompile(`("` + keysPattern + `"\s*:\s*)(?:"-1"|-1)([^0-9.eE]|$)`), `${1}"0"${2}`},
		// INI: clave = -1
		{regexp.MustCompile(`(?m)^([ \t]*` + keysPattern + `[ \t]*=[ \t]*)-1([ \t\r]*)$`), `${1}0${2}`},
		// XML de ajustes por objeto: <metadata key="clave" value="-1"/>
		{regexp.MustCompile(`(\bkey\s*=\s*"` + keysPattern + `"\s+value\s*=\s*")-1(")`), `${1}0${2}`},
	}
	errOutputExists = errors.New("output exists")
)

const maxScannedEntrySize = 256 << 20

type SanitizeError struct{ msg string }

func (e *SanitizeError) Error() string { return e.msg }

func sanitizeErrorf(format string, args ...any) error {
	return &SanitizeError{fmt.Sprintf(format, args...)}
}

type EntryFix struct {
	Name  string
	Count int
}

type Result struct {
	Source string
	Output string
	Fixes  []EntryFix
}

func (r Result) TotalFixes() int {
	total := 0
	for _, fix := range r.Fixes {
		total += fix.Count
	}
	return total
}

func (r Result) Describe() string {
	name := filepath.Base(r.Source)
	if r.Output == "" {
		return name + ": no necesitaba cambios"
	}
	return fmt.Sprintf("%s: %s → %s", name,
		plural(r.TotalFixes(), "ajuste corregido", "ajustes corregidos"), filepath.Base(r.Output))
}

func plural(count int, singular, pluralForm string) string {
	if count == 1 {
		return fmt.Sprintf("%d %s", count, singular)
	}
	return fmt.Sprintf("%d %s", count, pluralForm)
}

func sanitizeText(text string) (string, int) {
	total := 0
	for _, p := range patterns {
		count := len(p.re.FindAllStringIndex(text, -1))
		if count > 0 {
			text = p.re.ReplaceAllString(text, p.replacement)
			total += count
		}
	}
	return text, total
}

func sanitizeEntry(data []byte) ([]byte, int) {
	found := false
	for _, key := range fixedKeys {
		if bytes.Contains(data, []byte(key)) {
			found = true
			break
		}
	}
	if !found || !utf8.Valid(data) {
		return data, 0
	}
	text, count := sanitizeText(string(data))
	if count == 0 {
		return data, 0
	}
	return []byte(text), count
}

func shouldScan(f *zip.File) bool {
	name := strings.ToLower(f.Name)
	if strings.HasSuffix(name, "/") {
		return false
	}
	return strings.HasSuffix(name, ".config") || strings.HasSuffix(name, ".json") || strings.HasSuffix(name, ".xml")
}

func readEntry(f *zip.File) ([]byte, error) {
	if f.UncompressedSize64 > maxScannedEntrySize {
		return nil, fmt.Errorf("los ajustes superan el límite de %d MiB", maxScannedEntrySize>>20)
	}
	rc, err := f.Open()
	if err != nil {
		return nil, err
	}
	defer rc.Close()
	data, err := io.ReadAll(io.LimitReader(rc, maxScannedEntrySize+1))
	if err != nil {
		return nil, err
	}
	if len(data) > maxScannedEntrySize {
		return nil, fmt.Errorf("los ajustes superan el límite de %d MiB", maxScannedEntrySize>>20)
	}
	return data, nil
}

func defaultOutputPath(source, suffix string) string {
	ext := filepath.Ext(source)
	return strings.TrimSuffix(source, ext) + suffix + ext
}

func openZip(path string) (*zip.ReadCloser, error) {
	r, err := zip.OpenReader(path)
	// Los nombres "inseguros" solo importan al extraer; aquí se copian sin tocar el disco.
	if errors.Is(err, zip.ErrInsecurePath) && r != nil {
		return r, nil
	}
	return r, err
}

// sanitize3MF crea una copia corregida junto al original. Si no hay nada que corregir no escribe nada.
func sanitize3MF(source, suffix string) (Result, error) {
	source, err := filepath.Abs(source)
	if err != nil {
		return Result{}, err
	}
	result := Result{Source: source}

	info, err := os.Stat(source)
	if err != nil {
		if errors.Is(err, os.ErrNotExist) {
			return result, sanitizeErrorf("El archivo no existe")
		}
		return result, err
	}
	if !info.Mode().IsRegular() {
		return result, sanitizeErrorf("No es un archivo")
	}
	if !strings.EqualFold(filepath.Ext(source), ".3mf") {
		return result, sanitizeErrorf("No es un archivo .3mf")
	}

	reader, err := openZip(source)
	if err != nil {
		return result, sanitizeErrorf("No es un 3MF válido (%v)", err)
	}
	defer reader.Close()

	replacements := map[int][]byte{}
	for i, f := range reader.File {
		if !shouldScan(f) {
			continue
		}
		data, err := readEntry(f)
		if err != nil {
			return result, sanitizeErrorf("No se pudo leer %s: %v", f.Name, err)
		}
		if fixed, count := sanitizeEntry(data); count > 0 {
			replacements[i] = fixed
			result.Fixes = append(result.Fixes, EntryFix{f.Name, count})
		}
	}
	if len(replacements) == 0 {
		return result, nil
	}

	destination := defaultOutputPath(source, suffix)
	if _, err := os.Lstat(destination); err == nil {
		return result, outputExistsError(destination)
	}
	if err := writeArchive(&reader.Reader, info.Mode().Perm(), destination, replacements); err != nil {
		if errors.Is(err, errOutputExists) {
			return result, outputExistsError(destination)
		}
		return result, err
	}
	result.Output = destination
	return result, nil
}

func outputExistsError(destination string) error {
	return sanitizeErrorf("Ya existe %s. El original no se ha modificado.", filepath.Base(destination))
}

func writeArchive(reader *zip.Reader, mode os.FileMode, destination string, replacements map[int][]byte) (err error) {
	dir, base := filepath.Split(destination)
	tmp, err := os.CreateTemp(dir, "."+base+".*.tmp")
	if err != nil {
		return err
	}
	tmpName := tmp.Name()
	defer func() {
		if err != nil {
			tmp.Close()
			os.Remove(tmpName)
		}
	}()

	writer := zip.NewWriter(tmp)
	if err = writer.SetComment(reader.Comment); err != nil {
		return err
	}
	for i, f := range reader.File {
		data, replaced := replacements[i]
		if !replaced {
			// Copia sin descomprimir: el resto del 3MF queda idéntico.
			if err = writer.Copy(f); err != nil {
				return sanitizeErrorf("No se pudo copiar %s: %v", f.Name, err)
			}
			continue
		}
		header := &zip.FileHeader{
			Name:           f.Name,
			Comment:        f.Comment,
			Method:         f.Method,
			Modified:       f.Modified,
			CreatorVersion: f.CreatorVersion,
			ExternalAttrs:  f.ExternalAttrs,
		}
		var w io.Writer
		if w, err = writer.CreateHeader(header); err != nil {
			return sanitizeErrorf("No se pudo escribir %s: %v", f.Name, err)
		}
		if _, err = w.Write(data); err != nil {
			return err
		}
	}
	if err = writer.Close(); err != nil {
		return err
	}
	if err = tmp.Sync(); err != nil {
		return err
	}
	if err = tmp.Close(); err != nil {
		return err
	}
	if err = verifyArchive(tmpName); err != nil {
		return sanitizeErrorf("El archivo generado está dañado: %v", err)
	}
	if err = os.Chmod(tmpName, mode); err != nil {
		return err
	}
	return renameNoReplace(tmpName, destination)
}

func verifyArchive(path string) error {
	reader, err := openZip(path)
	if err != nil {
		return err
	}
	defer reader.Close()
	for _, f := range reader.File {
		rc, err := f.Open()
		if err != nil {
			return fmt.Errorf("%s: %w", f.Name, err)
		}
		_, err = io.Copy(io.Discard, rc)
		rc.Close()
		if err != nil {
			return fmt.Errorf("%s: %w", f.Name, err)
		}
	}
	return nil
}
