# Intentionally bad code for testing X-code
def bad_function(a, b, c, d, e, f):
    # Too many parameters - should trigger warning
    if a > 0:
        if b > 0:
            if c > 0:
                if d > 0:
                    # Too much nesting
                    return "nested"
    # SQL injection vulnerability
    query = "SELECT * FROM users WHERE id = " + str(a)
    # Unused variable
    unused_var = "test"
    return query
def complex_logic(x):
    # High complexity
    result = 0
    for i in range(10):
        for j in range(10):
            for k in range(10):
                if i > j:
                    if j > k:
                        result += i * j * k
    return result
