"""A 1A2B (Bulls and Cows) game implementation with a FastAPI interface."""
from __future__ import annotations

import random
from pathlib import Path
from typing import Tuple

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field, validator


def generate_secret_number() -> str:
    """Generate a four-digit number with unique digits as the secret."""
    digits = random.sample(range(10), 4)
    return "".join(map(str, digits))


def evaluate_guess(secret_number: str, guess: str) -> Tuple[int, int]:
    """Compare *guess* against *secret_number* and return the (A, B) counts.

    *A* counts the digits that are both correct and in the correct position.
    *B* counts the digits that are correct but in the wrong position.
    """
    if len(secret_number) != 4 or len(guess) != 4:
        raise ValueError("Both secret_number and guess must be 4 digits long.")

    secret_digits = list(secret_number)
    guess_digits = list(guess)

    count_a = 0
    count_b = 0

    for secret_digit, guess_digit in zip(secret_digits, guess_digits):
        if secret_digit == guess_digit:
            count_a += 1
        elif guess_digit in secret_digits:
            count_b += 1

    return count_a, count_b


class GuessRequest(BaseModel):
    secret: str = Field(..., min_length=4, max_length=4, pattern=r"^\d{4}$")
    guess: str = Field(..., min_length=4, max_length=4, pattern=r"^\d{4}$")

    @validator("secret", "guess")
    def digits_must_be_unique(cls, value: str) -> str:  # noqa: N805 - required by Pydantic
        if len(set(value)) != len(value):
            raise ValueError("Digits must be unique in secret and guess numbers.")
        return value


class GuessResponse(BaseModel):
    a: int = Field(..., ge=0, le=4, description="Correct digit in the correct position")
    b: int = Field(..., ge=0, le=4, description="Correct digit in the wrong position")


class SecretResponse(BaseModel):
    secret: str = Field(..., min_length=4, max_length=4, pattern=r"^\d{4}$")


app = FastAPI(title="1A2B Game API", description="Evaluate guesses for the 1A2B game.")

_INDEX_HTML_PATH = Path(__file__).resolve().parent / "templates" / "index.html"
_INDEX_HTML = _INDEX_HTML_PATH.read_text(encoding="utf-8")


@app.get("/", response_class=HTMLResponse)
def read_index() -> HTMLResponse:
    """Serve the single-page interface for playing the 1A2B game."""
    return HTMLResponse(content=_INDEX_HTML)


@app.get("/secret", response_model=SecretResponse)
def create_secret() -> SecretResponse:
    """Return a randomly generated secret number with unique digits."""
    secret = generate_secret_number()
    return SecretResponse(secret=secret)


@app.post("/guess", response_model=GuessResponse)
def evaluate_guess_endpoint(payload: GuessRequest) -> GuessResponse:
    """Evaluate the player's guess against the provided secret number."""
    if payload.secret == payload.guess:
        return GuessResponse(a=4, b=0)

    try:
        count_a, count_b = evaluate_guess(payload.secret, payload.guess)
    except ValueError as exc:  # pragma: no cover - defensive guard for runtime use
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return GuessResponse(a=count_a, b=count_b)


def play_game() -> None:
    """Play an interactive 1A2B game in the terminal."""
    secret_number = generate_secret_number()
    attempts = 0

    print("Welcome to the 1A2B game! Guess the 4-digit secret number with unique digits.")

    while True:
        guess = input("Enter a 4-digit number (unique digits): ")
        if len(guess) != 4 or not guess.isdigit() or len(set(guess)) != 4:
            print("Invalid input. Please enter four unique digits.")
            continue

        attempts += 1
        a, b = evaluate_guess(secret_number, guess)
        print(f"Result: {a}A{b}B")

        if a == 4:
            print(f"Congratulations! You guessed the secret number in {attempts} attempts.")
            break


if __name__ == "__main__":
    play_game()
