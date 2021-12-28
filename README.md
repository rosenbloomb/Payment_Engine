# Payment_Engine

Run it: python3 payment_engine.py <input file>

Test it: pytest -v 

Assumptions: All input values are positive. Only deposits can be disputed/resolved/charged back

The included .csv files give identical results. One has a header line, the other does not.
The output from running on the included .csv file should be:

1, 4.0, 0, 4.0, False

2, 8.0, 0, 8.0, False

3, 0.0, 10.0, 10.0, False

4, 0.0, 0.0, 0.0, True
