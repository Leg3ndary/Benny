import detoxify



results = detoxify.Detoxify('unbiased').predict('Hello there! How are you doing today?')

#results = detoxify.Detoxify('unbiased')

print(type(results))
print(results)

