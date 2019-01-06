import random

expr = ['/', '*', '-', '*', '%']

res = []
for _ in range(10):
    res.append('({})'.format(random.randint(-2000, +2000)))
    res.append(random.choice(expr))

res.pop()


p = """
int main() {{
    printInt({});
    return 0;
}}
""".format(' '.join(map(str, res)))

print (p)

res = [x if x != '/' else '//' for x in res]

exec('x =' + ' '.join(map(str, res)))
print('//', x)
