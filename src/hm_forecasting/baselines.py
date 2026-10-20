# a classic baseline (TSB)
def tsb_rate(target, alpha=0.1, beta=0.1):
    probability = 1.0
    size = float(target[0])

    for value in target[1:]:
        occurred = value > 0
        probability += beta * (float(occurred) - probability)
        if occurred:
            size += alpha * (value - size)

    return probability * size

