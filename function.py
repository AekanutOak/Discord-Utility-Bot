def divide_into_n_groups(input_list, n):
    if len(input_list) < n:
        return "Not enough elements to form {} groups.".format(n)

    group_size = len(input_list) // n
    remainder = len(input_list) % n

    groups = []

    start = 0
    for i in range(n):
        group_end = start + group_size + (1 if i < remainder else 0)
        groups.append(input_list[start:group_end])
        start = group_end

    return groups

# Example usage:
input_list = [1, 2, 3, 4]
n = 5
result = divide_into_n_groups(input_list, n)
print(result)