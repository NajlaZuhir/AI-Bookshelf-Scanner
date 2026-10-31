"""Extract readable books using OpenRouter structured output."""

import base64
import json
from pathlib import Path

from pydantic import ValidationError

if __package__:
    from .detection_schemas import BookDetectionResult
    from ..config import (
        OPENROUTER_MODEL,
        get_openrouter_client,
    )
else:
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from src.integrations.detection_schemas import BookDetectionResult
    from src.config import (
        OPENROUTER_MODEL,
        get_openrouter_client,
    )


def identify_books_in_image(image_path: Path | str) -> dict:  # Accept the image path
    # Read and encode the image
    image_base64 = base64.b64encode( # represents bytes using Base64.
        Path(image_path).read_bytes() # reads the image’s binary content.
        ).decode("ascii") # converts the encoded bytes into a text string that can be included in the JSON request.

    # Create the model request
    response = get_openrouter_client().chat.completions.create( 
        model=OPENROUTER_MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Identify readable books in this bookshelf photograph. "
                            "Return a JSON object with a 'books' array containing "
                            "'book_number', 'title' and 'author' for each book. Read books from "
                            "left to right, shelf by shelf from top to bottom. "
                            "Do not guess unreadable titles or authors. "
                            "If a title is unreadable, omit that book. "
                            "If an author is unreadable, use null. "
                            "If no titles are readable, return {\"books\": []}."
                        ),
                    },
                    {
                        "type": "image_url",
                        "image_url": { 
                            # This is a data URL containing the image itself. 
                            # It identifies the content as a JPEG encoded in Base64;
                            # it is not a link to an image hosted online.
                            "url": "data:image/jpeg;base64," + image_base64,
                        },
                    },
                ],
            }
        ],
        response_format={
            # Specify the expected response structure
            "type": "json_schema",
            "json_schema": {
                "name": "book_detection",
                "strict": True,
                "schema": BookDetectionResult.model_json_schema(),
            },
        },
        # Reject providers that would silently ignore the requested format.
        extra_body={"provider": {"require_parameters": True}},
    )

    if not response.choices:
        raise ValueError("OpenRouter returned no response choices.")

    choice = response.choices[0]

    # Validate the returned JSON locally
    try:
        result = BookDetectionResult.model_validate_json(
            choice.message.content, strict=True
        )
    except ValidationError as exc:
        raise ValueError("Model response did not match the expected books schema.") from exc

    # Return a normal Python dictionary
    return result.model_dump()

# Usage example
if __name__ == "__main__":
    # python -m src.integrations.openrouter_client
    image_path = Path(__file__).resolve().parents[2] / "data" / "book_1.jpg"
    result = identify_books_in_image(image_path)
    print(json.dumps(result, indent=2, ensure_ascii=False))
