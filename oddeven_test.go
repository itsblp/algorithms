package algorithms

import (
	"testing"
)

var data = map[int]bool{
	0: true,
	1: false,
	2: true,
	3: false,
	4: true,
	5: false,
}

func prettyPrint(even bool) string {
	if even {
		return "even"
	}
	return "odd"
}
func TestIsEven(t *testing.T) {
	for n, expected := range data {
		actual := IsEven(n)
		if expected != actual {
			t.Errorf("expected %d to be %s but IsEven() said it's %s", n, prettyPrint(expected), prettyPrint(actual))
		}
	}
}
