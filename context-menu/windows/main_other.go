//go:build !windows

package main

import (
	"fmt"
	"os"
)

// Versión de terminal para probar en Linux la misma lógica que usa el .exe.
func main() {
	exitCode := 0
	for _, file := range os.Args[1:] {
		result, err := sanitize3MF(file, defaultSuffix)
		if err != nil {
			fmt.Fprintf(os.Stderr, "[ERROR] %s: %v\n", file, err)
			exitCode = 1
			continue
		}
		fmt.Println("[OK]", result.Describe())
	}
	os.Exit(exitCode)
}
