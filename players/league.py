import math
from typing import List, Dict
from collections import defaultdict
import random


class Match:
    def __init__(self, team1: str, team2: str):
        self.team1 = team1
        self.team2 = team2
        self.score1 = None
        self.score2 = None

    def set_scores(self, score1: int, score2: int):
        if max(score1, score2) > 30:
            raise ValueError("Score cannot exceed 30.")
        self.score1 = score1
        self.score2 = score2

    def winner(self):
        if self.score1 is None or self.score2 is None:
            return None
        return self.team1 if self.score1 > self.score2 else self.team2


class TournamentManager:
    def __init__(self, team_list: List[str]):
        if len(team_list) < 3:
            raise ValueError("At least 3 teams are required to form a league.")
        self.teams = team_list
        self.groups = []
        self.group_matches = {}  # group_name -> List[Match]
        self.group_results = {}  # group_name -> List[(team, stats)]
        self.knockout_qualifiers = []

    def group_teams(self):
        teams = self.teams[:]
        group_id = 1
        i = 0

        while i + 3 <= len(teams):
            group_teams = teams[i:i+3]
            self.groups.append({
                'name': f'Group {group_id}',
                'teams': group_teams,
                'type': 'standard',
                'qualifiers': 2
            })
            i += 3
            group_id += 1

        remaining = teams[i:]

        if len(remaining) == 1:
            self.groups[-1]['teams'].append(remaining[0])
            self.groups[-1]['type'] = 'four-team'
        elif len(remaining) == 2:
            self.groups.append({
                'name': f'Group {group_id}',
                'teams': remaining,
                'type': 'head-to-head',
                'qualifiers': 1
            })

    def schedule_group_matches(self):
        for group in self.groups:
            teams = group['teams']
            matches = []
            for i in range(len(teams)):
                for j in range(i + 1, len(teams)):
                    matches.append(Match(teams[i], teams[j]))
            self.group_matches[group['name']] = matches

    def update_score(self, group_name: str, team1: str, team2: str, score1: int, score2: int):
        matches = self.group_matches.get(group_name, [])
        for match in matches:
            if {match.team1, match.team2} == {team1, team2}:
                match.set_scores(score1, score2)
                return
        raise ValueError(f"Match not found: {team1} vs {team2} in {group_name}")

    def calculate_group_results(self):
        for group in self.groups:
            group_name = group['name']
            standings = defaultdict(lambda: {'wins': 0, 'points': 0})
            for match in self.group_matches[group_name]:
                if match.score1 is None or match.score2 is None:
                    continue
                standings[match.team1]['points'] += match.score1
                standings[match.team2]['points'] += match.score2
                winner = match.winner()
                if winner:
                    standings[winner]['wins'] += 1
            sorted_teams = sorted(standings.items(), key=lambda x: (x[1]['wins'], x[1]['points']), reverse=True)
            self.group_results[group_name] = {
                'standings': sorted_teams,
                'qualifiers': [team for team, _ in sorted_teams[:group['qualifiers']]]
            }

        self.knockout_qualifiers = [team for result in self.group_results.values() for team in result['qualifiers']]

    def generate_knockout_bracket(self) -> Dict:
        total_teams = len(self.knockout_qualifiers)
        bracket_size = 1 << (total_teams - 1).bit_length()
        byes = bracket_size - total_teams
        return {
            'qualified_teams': self.knockout_qualifiers,
            'bracket_size': bracket_size,
            'number_of_byes': byes,
            'rounds': int(math.log2(bracket_size))
        }

    def print_group_stage(self):
        print("🏅 Group Stage:")
        for group in self.groups:
            print(f"{group['name']} ({group['type']}): {group['teams']} → Qualifiers: {group['qualifiers']}")

    def print_group_results(self):
        print("\n📊 Group Results:")
        for group_name, result in self.group_results.items():
            print(f"{group_name}:")
            for team, stats in result['standings']:
                print(f"  - {team}: {stats['wins']} wins, {stats['points']} points")
            print(f"✅ Qualifiers: {result['qualifiers']}")
