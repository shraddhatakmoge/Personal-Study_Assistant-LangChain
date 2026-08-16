from app.tools.calculator import calculator


def test_calculator():
    result = calculator.invoke({
        "expression": "25 * 16"
    })

    assert result == "400"