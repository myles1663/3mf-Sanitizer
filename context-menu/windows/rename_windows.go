//go:build windows

package main

import (
	"errors"

	"golang.org/x/sys/windows"
)

func renameNoReplace(from, to string) error {
	fromPtr, err := windows.UTF16PtrFromString(from)
	if err != nil {
		return err
	}
	toPtr, err := windows.UTF16PtrFromString(to)
	if err != nil {
		return err
	}
	// Sin MOVEFILE_REPLACE_EXISTING falla si el destino ya existe.
	err = windows.MoveFileEx(fromPtr, toPtr, windows.MOVEFILE_WRITE_THROUGH)
	if errors.Is(err, windows.ERROR_ALREADY_EXISTS) || errors.Is(err, windows.ERROR_FILE_EXISTS) {
		return errOutputExists
	}
	return err
}
