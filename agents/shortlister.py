
def shortlist(candidates, threshold=50):
    return [c for c in candidates if c['score'] >= threshold]

