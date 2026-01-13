from fastmcp import FastMCP
import math

mcp = FastMCP("Calculator MCP Server")

# ---------------- BASIC OPERATIONS ----------------

@mcp.tool()
def add(a: float, b: float) -> float:
    """Add two numbers"""
    return a + b

@mcp.tool()
def subtract(a: float, b: float) -> float:
    """Subtract b from a"""
    return a - b

@mcp.tool()
def multiply(a: float, b: float) -> float:
    """Multiply two numbers"""
    return a * b

@mcp.tool()
def divide(a: float, b: float) -> float:
    """Divide a by b"""
    if b == 0:
        raise ValueError("Division by zero is not allowed")
    return a / b

# ---------------- ADVANCED OPERATIONS ----------------

@mcp.tool()
def modulus(a: int, b: int) -> int:
    """Modulus (remainder)"""
    if b == 0:
        raise ValueError("Modulus by zero is not allowed")
    return a % b

@mcp.tool()
def percentage(a: float, b: float) -> float:
    """Calculate percentage (a % of b)"""
    return (a / 100) * b

@mcp.tool()
def power(a: float, b: float) -> float:
    """a raised to the power b"""
    return a ** b

@mcp.tool()
def sqrt(a: float) -> float:
    """Square root of a number"""
    if a < 0:
        raise ValueError("Square root of negative number is not allowed")
    return math.sqrt(a)

# ---------------- RUN SERVER ----------------

if __name__ == "__main__":
    mcp.run()
