//go:build !windows

package main

import (
	"errors"
	"os"
)

func renameNoReplace(from, to string) error {
	if err := os.Link(from, to); err != nil {
		if errors.Is(err, os.ErrExist) {
			return errOutputExists
		}
		return err
	}
	return os.Remove(from)
}
