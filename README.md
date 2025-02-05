# ShotGeek

![ShotGeek-display](https://github.com/user-attachments/assets/a6d0e3c6-1d8f-407f-a6ac-e645a631e4ed)


## Table of Contents
1. [Introduction](#shotgeek)
2. [Features](#features)
3. [Getting Started](#getting-started)
   - [Prerequisites](#prerequisites)
   - [Installation](#installation)
4. [Usage](#usage)
   - [Searching for a Player](#searching-for-a-player)
   - [Comparing Players](#comparing-players)
   - [Viewing Graphs](#viewing-graphs)
5. [Contributing](#contributing)
6. [License](#license)

## ShotGeek

ShotGeek is a Django web application that provides NBA stats, scores, and player comparisons. Whether you're a casual fan or a stats enthusiast, ShotGeek helps you explore player performance and compare careers with detailed tables and visualizations.

## Features
- **Player Search**: Look up any NBA player by full name to access their career statistics.
- **Career Stat Totals**: View detailed career stats for individual players.
- **Graphical Analysis**: Use interactive graphs to visualize player performance over time.
- **Player Comparison**: Compare two players' career stats side by side.
- **Customizable Views**: Select stat categories for table and graph comparisons.

## Getting Started
### Prerequisites
Ensure you have the following installed on your system:
- Python 3.x
- Django
- PostgreSQL (or an alternative database)

### Installation
1. Clone the repository:
   ```sh
   git clone https://github.com/yourusername/shotgeek.git
   cd shotgeek
   ```
2. Create and activate a virtual environment:
   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```
3. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
4. Set up the database:
   ```sh
   python manage.py migrate
   ```
5. Run the development server:
   ```sh
   python manage.py runserver
   ```
6. Open your browser and visit: `http://127.0.0.1:8000/`

## Usage
### Searching for a Player
- Enter the player's full name in the search bar.
- Ensure correct spelling to avoid incorrect results.
- Example: Searching for `Charles Barkley` will take you to his player page.

### Comparing Players
- Click the **Compare Players** button to access the comparison tool.
- Enter the full name of two players to compare their stats side by side.
- Select specific stat categories for in-depth analysis.

### Viewing Graphs
- Navigate to a player's page or the comparison page.
- Use the dropdown menu to select a stat category.
- The graph will display trends over the player's career.

## Contributing

We welcome contributions from the open-source community. If you find any issues or want to suggest enhancements, feel free to create a pull request or submit an issue.
For more information on contributing visit [https://github.com/Kudzmat/NoseBleedSection/blob/master/CONTRIBUTING.md](CONTRIBUTING.md)

## License

ShotGeek is licensed under the [Apache License 2.0](LICENSE).


