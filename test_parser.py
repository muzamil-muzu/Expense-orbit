import sys
import os

# add parent directory to sys path so we can import app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'Expense-tracker-pro-main')))

from app import parse_sms

def run_tests():
    # Test 1: The provided example
    test1 = "Rs.450 debited from A/C XXXX via UPI to Swiggy"
    res1 = parse_sms(test1)
    print("Test 1 Result:", res1)
    assert res1["amount"] == 450.0
    assert res1["merchant"] == "Swiggy"
    assert res1["category"] == "Food"
    assert res1["payment_mode"] == "UPI"

    # Test 2: Another format with INR
    test2 = "INR 1,200.50 spent at Amazon on 12-Mar via Card."
    res2 = parse_sms(test2)
    print("Test 2 Result:", res2)
    assert res2["amount"] == 1200.50
    assert res2["merchant"] == "Amazon"
    assert res2["category"] == "Shopping"
    assert res2["payment_mode"] == "Card"

    # Test 3: Unknown merchant
    test3 = "₹ 50.00 to Local Grocery Store via UPI"
    res3 = parse_sms(test3)
    print("Test 3 Result:", res3)
    assert res3["amount"] == 50.0
    assert res3["merchant"] == "Local Grocery Store"
    assert res3["category"] == "Others"
    assert res3["payment_mode"] == "UPI"

    print("ALL TESTS PASSED!")

if __name__ == "__main__":
    run_tests()
