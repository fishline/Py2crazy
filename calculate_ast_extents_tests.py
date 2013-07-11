# minimized weird-looking tests from Python standard lib

# from Lib/fractions.py
def foo():
    return Fraction(a._denominator ** -power,
                    a._numerator ** -power)

# from Lib/doctest.py
self.val = self.val ** 2

# from Lib/threading.py
@name.setter
def name(self, name):
    pass

# from Lib/csv.py
@fieldnames.setter
def fieldnames(self, value):
    self._fieldnames = value
