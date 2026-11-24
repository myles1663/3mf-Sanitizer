package main

import (
	"archive/zip"
	"bytes"
	"errors"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestSanitizeTextFixesAllFormats(t *testing.T) {
	source := `{"raft_first_layer_expansion": -1, "tree_support_wall_count": "-1"}` + "\n" +
		"raft_first_layer_expansion = -1\n" +
		`<metadata key="tree_support_wall_count" value="-1"/>` + "\n" +
		`{"tree_support_wall_count": -10}` + "\n"

	result, count := sanitizeText(source)

	if count != 4 {
		t.Fatalf("count = %d, want 4\n%s", count, result)
	}
	for _, want := range []string{
		`"raft_first_layer_expansion": "0"`,
		`"tree_support_wall_count": "0"`,
		"raft_first_layer_expansion = 0\n",
		`key="tree_support_wall_count" value="0"`,
		`"tree_support_wall_count": -10`,
	} {
		if !strings.Contains(result, want) {
			t.Errorf("result does not contain %q\n%s", want, result)
		}
	}
}

func TestSanitizeTextHandlesAdjacentAndTrailingValues(t *testing.T) {
	result, count := sanitizeText(`{"raft_first_layer_expansion":-1,"tree_support_wall_count":-1}`)
	if count != 2 || result != `{"raft_first_layer_expansion":"0","tree_support_wall_count":"0"}` {
		t.Fatalf("got %q (%d)", result, count)
	}
	result, count = sanitizeText(`"tree_support_wall_count": -1`)
	if count != 1 || result != `"tree_support_wall_count": "0"` {
		t.Fatalf("got %q (%d)", result, count)
	}
}

func TestSanitizeTextLeavesOtherValues(t *testing.T) {
	source := `{"raft_first_layer_expansion": 1, "other": -1, "tree_support_wall_count": -1.5}`
	if result, count := sanitizeText(source); count != 0 || result != source {
		t.Fatalf("got %q (%d)", result, count)
	}
}

func TestOversizedSettingsAreRejectedRatherThanSkipped(t *testing.T) {
	entry := &zip.File{FileHeader: zip.FileHeader{
		Name:               "Metadata/project_settings.config",
		UncompressedSize64: maxScannedEntrySize + 1,
	}}
	if !shouldScan(entry) {
		t.Fatal("oversized settings would be silently skipped")
	}
	if _, err := readEntry(entry); err == nil || !strings.Contains(err.Error(), "límite") {
		t.Fatalf("err = %v", err)
	}
}

const projectSettings = `{"raft_first_layer_expansion": "-1", "tree_support_wall_count": -1}`

func writeTestArchive(t *testing.T, path string, files map[string]string) {
	t.Helper()
	out, err := os.Create(path)
	if err != nil {
		t.Fatal(err)
	}
	w := zip.NewWriter(out)
	if err := w.SetComment("archive comment"); err != nil {
		t.Fatal(err)
	}
	for _, name := range []string{"3D/3dmodel.model", "Metadata/project_settings.config", "Metadata/plate_1.png"} {
		content, ok := files[name]
		if !ok {
			continue
		}
		method := zip.Deflate
		if strings.HasSuffix(name, ".png") {
			method = zip.Store
		}
		fw, err := w.CreateHeader(&zip.FileHeader{Name: name, Method: method})
		if err != nil {
			t.Fatal(err)
		}
		fw.Write([]byte(content))
	}
	if err := w.Close(); err != nil {
		t.Fatal(err)
	}
	out.Close()
}

func readArchive(t *testing.T, path string) (map[string]string, *zip.ReadCloser) {
	t.Helper()
	r, err := zip.OpenReader(path)
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { r.Close() })
	contents := map[string]string{}
	for _, f := range r.File {
		data, err := readEntry(f)
		if err != nil {
			t.Fatal(err)
		}
		contents[f.Name] = string(data)
	}
	return contents, r
}

func TestSanitize3MFCreatesCopyAndKeepsOriginal(t *testing.T) {
	dir := t.TempDir()
	source := filepath.Join(dir, "Modelo con espacios y ñ.3MF")
	writeTestArchive(t, source, map[string]string{
		"3D/3dmodel.model":                 "model data",
		"Metadata/project_settings.config": projectSettings,
		"Metadata/plate_1.png":             "png data",
	})
	original, _ := os.ReadFile(source)

	result, err := sanitize3MF(source, defaultSuffix)
	if err != nil {
		t.Fatal(err)
	}

	if want := filepath.Join(dir, "Modelo con espacios y ñ_sanitizado.3MF"); result.Output != want {
		t.Fatalf("output = %q, want %q", result.Output, want)
	}
	if result.TotalFixes() != 2 {
		t.Fatalf("fixes = %d, want 2", result.TotalFixes())
	}
	if after, _ := os.ReadFile(source); !bytes.Equal(after, original) {
		t.Fatal("original file was modified")
	}
	contents, r := readArchive(t, result.Output)
	if r.Comment != "archive comment" {
		t.Errorf("comment = %q", r.Comment)
	}
	if got := contents["Metadata/project_settings.config"]; got != `{"raft_first_layer_expansion": "0", "tree_support_wall_count": "0"}` {
		t.Errorf("settings = %q", got)
	}
	if contents["3D/3dmodel.model"] != "model data" || contents["Metadata/plate_1.png"] != "png data" {
		t.Error("unmodified entries changed")
	}
	if r.File[2].Method != zip.Store {
		t.Error("compression method of unmodified entry changed")
	}
	if !strings.Contains(result.Describe(), "2 ajustes corregidos → Modelo con espacios y ñ_sanitizado.3MF") {
		t.Errorf("describe = %q", result.Describe())
	}
	if leftovers, _ := filepath.Glob(filepath.Join(dir, ".*.tmp")); len(leftovers) > 0 {
		t.Errorf("temporary files left: %v", leftovers)
	}
}

func TestSanitize3MFWithoutChangesWritesNothing(t *testing.T) {
	dir := t.TempDir()
	source := filepath.Join(dir, "ok.3mf")
	writeTestArchive(t, source, map[string]string{"Metadata/project_settings.config": `{"tree_support_wall_count": "0"}`})

	result, err := sanitize3MF(source, defaultSuffix)
	if err != nil || result.Output != "" || result.TotalFixes() != 0 {
		t.Fatalf("result = %+v, err = %v", result, err)
	}
	if entries, _ := os.ReadDir(dir); len(entries) != 1 {
		t.Fatalf("unexpected files: %v", entries)
	}
}

func TestSanitize3MFDoesNotOverwriteExistingOutput(t *testing.T) {
	dir := t.TempDir()
	source := filepath.Join(dir, "model.3mf")
	writeTestArchive(t, source, map[string]string{"Metadata/project_settings.config": projectSettings})
	existing := filepath.Join(dir, "model_sanitizado.3mf")
	os.WriteFile(existing, []byte("keep"), 0o644)

	_, err := sanitize3MF(source, defaultSuffix)

	var sanitizeErr *SanitizeError
	if !errors.As(err, &sanitizeErr) || !strings.Contains(err.Error(), "Ya existe") {
		t.Fatalf("err = %v", err)
	}
	if data, _ := os.ReadFile(existing); string(data) != "keep" {
		t.Fatal("existing output was overwritten")
	}
}

func TestRenameNoReplaceRefusesExistingDestination(t *testing.T) {
	dir := t.TempDir()
	from, to := filepath.Join(dir, "from"), filepath.Join(dir, "to")
	os.WriteFile(from, []byte("new"), 0o644)
	os.WriteFile(to, []byte("old"), 0o644)
	if err := renameNoReplace(from, to); !errors.Is(err, errOutputExists) {
		t.Fatalf("err = %v", err)
	}
	if data, _ := os.ReadFile(to); string(data) != "old" {
		t.Fatal("destination was replaced")
	}
}

func TestSanitize3MFRejectsInvalidFiles(t *testing.T) {
	dir := t.TempDir()
	notZip := filepath.Join(dir, "bad.3mf")
	os.WriteFile(notZip, []byte("not a zip"), 0o644)
	wrongExt := filepath.Join(dir, "model.stl")
	os.WriteFile(wrongExt, []byte("solid"), 0o644)

	for _, path := range []string{notZip, wrongExt, filepath.Join(dir, "missing.3mf")} {
		var sanitizeErr *SanitizeError
		if _, err := sanitize3MF(path, defaultSuffix); !errors.As(err, &sanitizeErr) {
			t.Errorf("%s: err = %v", filepath.Base(path), err)
		}
	}
}
