# AI Book Shelf Scanner 

Identify books in a bookshelf photo and rank them based on the reader's preferences.

Run the CLI from the project root after configuring the database and API credentials:

```bash
python -m src.cli --image "data/book_5.jpg" --preference "I enjoy science fiction and fantasy novels" --top-k 3
```

Use `python -m src.cli --help` to see the available arguments. See the [manual integration guide](docs/manual_api_integration_testing.md) for database setup and API checks.

Development followed an iterative process:

Research → choose an approach → implement a component → test manually → integrate with the next stage.

See [Development stages](docs/development_stages.md) for the project’s progression and implementation details.

## Project structure

```text

├── src/                                  # Application code
│   │
│   ├── cli.py                            # Parses terminal arguments and runs the pipeline
│   ├── config.py                         # Loads provider settings and creates the OpenRouter client
│   │
│   ├── integrations/                     # External provider clients and detection models
│   │   ├── open_library_client.py        # Searches, matches, and retrieves Open Library metadata
│   │   ├── openrouter_client.py          # Identifies readable books in bookshelf images
│   │   └── detection_schemas.py          # Defines Pydantic models for detection output
│   │
│   ├── services/                         # Coordinates application workflows
│   │   ├── metadata_service.py           # Combines detection and metadata lookup with status counts
│   │   ├── recommendation_service.py     # Combines profile preparation, embeddings, and ranking
│   │   └── bookshelf_pipeline.py         # Coordinates scanning, database storage, and recommendations
│   │
│   ├── ml/                               # Content-based recommendation components
│   │   ├── preprocessing.py              # Validates inputs and prepares book text profiles
│   │   ├── embeddings.py                 # Generates normalized semantic embeddings
│   │   └── ranking.py                    # Calculates similarity and ranks books
│   │
│   ├── database/                         # PostgreSQL connections, schema, and data access
│   │   ├── connection.py                 # Opens connections using environment settings
│   │   ├── migrations/
│   │   │   └── 001_book_shelf_schema.sql  # Creates tables and their foreign keys
│   │   └── repositories/
│   │       ├── scan_repository.py        # Saves and retrieves scan records
│   │       ├── book_repository.py        # Saves and retrieves book metadata
│   │       └── recommendation_repository.py # Saves and retrieves recommendation results
│   │
│   └── api/                              # FastAPI application and HTTP endpoints
│       ├── main.py                       # Creates the app and registers route modules
│       ├── schemas.py                    # Defines and validates API request models
│       └── routes/
│           ├── scans.py                  # Creates and retrieves scan records
│           ├── books.py                  # Retrieves books and books belonging to a scan
│           └── recommendations.py        # Generates, saves, and retrieves recommendations
│   
├── tests/
│   └── test_repositories.py              # Integration tests using PostgreSQL
├── data/
│   ├── book_*.jpg                        # Sample bookshelf photos, numbered 1 through 11
│   └── processed/
│       └── books_metadata.json           # JSON output from the standalone metadata example
│   
├── docs/
│   ├── development_stages.md             # Implementation stages and design decisions
│   └── manual_api_integration_testing.md # Manual checks for the CLI, database, and API
│   
├── .env                                  # Local credentials and configuration
├── .env.example                          # Configuration template without real credentials
├── .gitignore                            # Git ignore rules
├── requirements.txt                      # Python dependencies
└── README.md                             # Project overview and usage
```

The CLI pipeline saves scans, matched books, and recommendations to PostgreSQL.
The JSON file in `data/processed/` is output from the standalone metadata example;
it is not required by the CLI pipeline.
