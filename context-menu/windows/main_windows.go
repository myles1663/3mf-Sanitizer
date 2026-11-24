//go:build windows

package main

import (
	"errors"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"

	"golang.org/x/sys/windows"
	"golang.org/x/sys/windows/registry"
)

const (
	appName   = "Sanitizador 3MF"
	menuLabel = "Sanitizar 3MF"
	exeName   = "Sanitizador3MF.exe"

	verbKey      = `Software\Classes\SystemFileAssociations\.3mf\shell\Sanitizador3MF`
	uninstallKey = `Software\Microsoft\Windows\CurrentVersion\Uninstall\Sanitizador3MF`

	idYes = 6
	idNo  = 7
)

// Se fija al compilar con -ldflags "-X main.appVersion=...".
var appVersion = "dev"

var (
	shell32            = windows.NewLazySystemDLL("shell32.dll")
	procSHChangeNotify = shell32.NewProc("SHChangeNotify")
)

func main() {
	args := os.Args[1:]
	switch {
	case len(args) == 0:
		runSetup()
	case args[0] == "--install":
		install()
	case args[0] == "--uninstall":
		uninstall()
	default:
		files := args
		if args[0] == "--" {
			files = args[1:]
		}
		os.Exit(sanitizeFiles(files))
	}
}

func messageBox(text string, flags uint32) int32 {
	textPtr, _ := windows.UTF16PtrFromString(text)
	titlePtr, _ := windows.UTF16PtrFromString(appName)
	result, _ := windows.MessageBox(0, textPtr, titlePtr, flags|windows.MB_SETFOREGROUND|windows.MB_TOPMOST)
	return result
}

func showError(text string) {
	messageBox(text, windows.MB_OK|windows.MB_ICONERROR)
}

func sanitizeFiles(files []string) int {
	if len(files) == 0 {
		showError("Selecciona al menos un archivo .3mf.")
		return 1
	}
	var lines []string
	sanitized, unchanged, failed := 0, 0, 0
	for _, file := range files {
		result, err := sanitize3MF(file, defaultSuffix)
		switch {
		case err != nil:
			failed++
			var sanitizeErr *SanitizeError
			message := err.Error()
			if !errors.As(err, &sanitizeErr) {
				message = "Error: " + message
			}
			lines = append(lines, filepath.Base(file)+": "+message)
		case result.Output == "":
			unchanged++
			lines = append(lines, result.Describe())
		default:
			sanitized++
			lines = append(lines, result.Describe())
		}
	}

	var title string
	switch {
	case len(files) == 1 && failed == 1:
		title = "No se pudo sanitizar el 3MF"
	case len(files) == 1 && sanitized == 1:
		title = "3MF sanitizado"
	case len(files) == 1:
		title = "El 3MF ya era compatible"
	default:
		parts := []string{plural(sanitized, "sanitizado", "sanitizados"), plural(unchanged, "sin cambios", "sin cambios")}
		if failed > 0 {
			parts = append(parts, plural(failed, "error", "errores"))
		}
		title = fmt.Sprintf("%d archivos: %s", len(files), strings.Join(parts, ", "))
	}

	icon := uint32(windows.MB_ICONINFORMATION)
	if failed > 0 {
		icon = windows.MB_ICONERROR
	}
	messageBox(title+"\n\n"+strings.Join(lines, "\n"), windows.MB_OK|icon)
	if failed > 0 {
		return 1
	}
	return 0
}

func installedExe() (string, error) {
	dir, err := windows.KnownFolderPath(windows.FOLDERID_LocalAppData, 0)
	if err != nil {
		return "", fmt.Errorf("no se pudo localizar la carpeta de aplicaciones del usuario: %w", err)
	}
	if dir == "" {
		return "", errors.New("la carpeta de aplicaciones del usuario está vacía")
	}
	return filepath.Join(dir, "Programs", "Sanitizador3MF", exeName), nil
}

func samePath(a, b string) bool {
	return a != "" && b != "" && strings.EqualFold(filepath.Clean(a), filepath.Clean(b))
}

func isInstalled() (bool, error) {
	key, err := registry.OpenKey(registry.CURRENT_USER, verbKey+`\command`, registry.QUERY_VALUE)
	if errors.Is(err, registry.ErrNotExist) {
		return false, nil
	}
	if err != nil {
		return false, err
	}
	key.Close()
	return true, nil
}

func isWindows11() bool {
	return windows.RtlGetVersion().BuildNumber >= 22000
}

func runSetup() {
	installed, err := isInstalled()
	if err != nil {
		showError("No se pudo comprobar la instalación:\n\n" + err.Error())
		os.Exit(1)
	}
	if installed {
		current, err := os.Executable()
		if err != nil {
			showError("No se pudo localizar el ejecutable actual:\n\n" + err.Error())
			os.Exit(1)
		}
		destination, err := installedExe()
		if err != nil {
			showError(err.Error())
			os.Exit(1)
		}
		if samePath(current, destination) {
			if messageBox("«"+menuLabel+"» ya está en el menú del botón derecho de los archivos .3mf.\n\n¿Quieres quitarlo?",
				windows.MB_YESNO|windows.MB_ICONQUESTION) == idYes {
				uninstall()
			}
			return
		}
		switch messageBox("«"+menuLabel+"» ya está instalado.\n\n"+
			"Sí: reinstalar o actualizar\nNo: desinstalar\nCancelar: no hacer nada",
			windows.MB_YESNOCANCEL|windows.MB_ICONQUESTION) {
		case idYes:
			install()
		case idNo:
			uninstall()
		}
		return
	}

	if messageBox("¿Añadir «"+menuLabel+"» al menú del botón derecho de los archivos .3mf?\n\n"+
		"Corrige raft_first_layer_expansion y tree_support_wall_count = -1 en proyectos de MakerWorld/Bambu Lab. "+
		"Crea una copia «_sanitizado.3mf» y nunca modifica el original.\n\n"+
		"No requiere permisos de administrador.",
		windows.MB_YESNO|windows.MB_ICONQUESTION) == idYes {
		install()
	}
}

func install() {
	exe, err := copySelf()
	if err != nil {
		showError("No se pudo instalar:\n\n" + err.Error())
		os.Exit(1)
	}
	if err := registerMenu(exe); err != nil {
		showError("No se pudo completar la instalación del menú contextual:\n\n" + err.Error() +
			"\n\nVuelve a ejecutar el instalador para reintentarlo.")
		os.Exit(1)
	}
	notifyShell()

	message := "Listo. Haz clic derecho sobre un archivo .3mf y elige «" + menuLabel + "»."
	if isWindows11() {
		message = "Listo. Haz clic derecho sobre un archivo .3mf → «Mostrar más opciones» → «" + menuLabel + "»."
	}
	message += "\n\nLa opción queda instalada; no necesitas volver a abrir este instalador.\n\n" +
		"Para desinstalarlo: Configuración → Aplicaciones → " + appName + "."
	messageBox(message, windows.MB_OK|windows.MB_ICONINFORMATION)
}

func copySelf() (string, error) {
	source, err := os.Executable()
	if err != nil {
		return "", err
	}
	destination, err := installedExe()
	if err != nil {
		return "", err
	}
	if samePath(source, destination) {
		return destination, nil
	}
	dir := filepath.Dir(destination)
	if err := os.MkdirAll(dir, 0o755); err != nil {
		return "", err
	}

	in, err := os.Open(source)
	if err != nil {
		return "", err
	}
	defer in.Close()
	tmp, err := os.CreateTemp(dir, ".Sanitizador3MF.*.tmp")
	if err != nil {
		return "", err
	}
	_, copyErr := io.Copy(tmp, in)
	closeErr := tmp.Close()
	if copyErr == nil {
		copyErr = closeErr
	}
	if copyErr == nil {
		copyErr = os.Rename(tmp.Name(), destination)
	}
	if copyErr != nil {
		os.Remove(tmp.Name())
		return "", fmt.Errorf("%w\n\nSi "+appName+" se está ejecutando, ciérralo e inténtalo de nuevo.", copyErr)
	}
	return destination, nil
}

func setStrings(path string, values map[string]string) error {
	key, _, err := registry.CreateKey(registry.CURRENT_USER, path, registry.SET_VALUE)
	if err != nil {
		return err
	}
	defer key.Close()
	for name, value := range values {
		if err := key.SetStringValue(name, value); err != nil {
			return err
		}
	}
	return nil
}

func registerMenu(exe string) error {
	info, err := os.Stat(exe)
	if err != nil {
		return err
	}
	if err := setStrings(verbKey, map[string]string{
		"MUIVerb":          menuLabel,
		"Icon":             `"` + exe + `",0`,
		"MultiSelectModel": "Document",
	}); err != nil {
		return err
	}
	if err := setStrings(verbKey+`\command`, map[string]string{"": `"` + exe + `" -- "%1"`}); err != nil {
		return err
	}

	if err := setStrings(uninstallKey, map[string]string{
		"DisplayName":     appName,
		"DisplayVersion":  appVersion,
		"DisplayIcon":     `"` + exe + `",0`,
		"InstallLocation": filepath.Dir(exe),
		"UninstallString": `"` + exe + `" --uninstall`,
	}); err != nil {
		return err
	}
	key, err := registry.OpenKey(registry.CURRENT_USER, uninstallKey, registry.SET_VALUE)
	if err != nil {
		return err
	}
	defer key.Close()
	if err := key.SetDWordValue("EstimatedSize", uint32((info.Size()+1023)/1024)); err != nil {
		return err
	}
	if err := key.SetDWordValue("NoModify", 1); err != nil {
		return err
	}
	return key.SetDWordValue("NoRepair", 1)
}

func deleteKeyTree(path string) error {
	key, err := registry.OpenKey(registry.CURRENT_USER, path, registry.ENUMERATE_SUB_KEYS)
	if errors.Is(err, registry.ErrNotExist) {
		return nil
	}
	if err != nil {
		return err
	}
	names, err := key.ReadSubKeyNames(-1)
	key.Close()
	if err != nil {
		return err
	}
	for _, name := range names {
		if err := deleteKeyTree(path + `\` + name); err != nil {
			return err
		}
	}
	err = registry.DeleteKey(registry.CURRENT_USER, path)
	if errors.Is(err, registry.ErrNotExist) {
		return nil
	}
	return err
}

func uninstall() {
	exe, err := installedExe()
	if err != nil {
		showError(err.Error())
		os.Exit(1)
	}
	current, err := os.Executable()
	if err != nil {
		showError("No se pudo localizar el ejecutable actual:\n\n" + err.Error())
		os.Exit(1)
	}
	var failures []string
	for _, path := range []string{verbKey, uninstallKey} {
		if err := deleteKeyTree(path); err != nil {
			failures = append(failures, path+": "+err.Error())
		}
	}
	notifyShell()

	deleteSelf := samePath(current, exe)
	if !deleteSelf {
		if err := os.Remove(exe); err != nil && !errors.Is(err, os.ErrNotExist) {
			failures = append(failures, err.Error())
		}
		if err := os.Remove(filepath.Dir(exe)); err != nil && !errors.Is(err, os.ErrNotExist) {
			failures = append(failures, err.Error())
		}
	}

	if len(failures) > 0 {
		showError("La desinstalación no se completó:\n\n" + strings.Join(failures, "\n"))
		os.Exit(1)
	}
	message := "«" + menuLabel + "» se ha quitado del menú contextual."
	if deleteSelf {
		message += "\n\nEl ejecutable está en uso. Después de cerrar esta ventana puedes borrar:\n\n" + exe
	}
	messageBox(message, windows.MB_OK|windows.MB_ICONINFORMATION)
}

func notifyShell() {
	const shcneAssocChanged = 0x08000000
	procSHChangeNotify.Call(shcneAssocChanged, 0, 0, 0)
}
