def clean_text(text: str) -> str:
    lines = [
        line.strip()
        for line in text.splitlines()
    ]

    lines = [
        line
        for line in lines
        if line
    ]

    print("Before:", len(text))
    print("After :", len("\n".join(lines)))

    return "\n".join(lines)


