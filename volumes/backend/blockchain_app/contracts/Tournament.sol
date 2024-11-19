// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract TournamentManager {
    
    // Structure to store tournament information
    struct Tournament {
        uint256 id;
        // users id disaplayed names
        bytes32[] users_name;

        // Mapping of user name to their score
        mapping(bytes32 => uint256) scores;
        // Flag to check if tournament exists
        bool exists; 
    }


    // Mapping to store tournaments by ID
    mapping(uint256 => Tournament) public tournaments;

    // Event to notify when a tournament is created or a score is updated
    event TournamentCreated(uint256 tournamentId, bytes32[] users_name);
    event ScoreUpdated(uint256 tournamentId, bytes32 user, uint256 newScore);

    // Function to create a tournament
    function createTournament(uint256 _tournamentId, bytes32[] memory users_name) public {
        require(!tournaments[_tournamentId].exists, "Tournament already exists");

        Tournament storage newTournament = tournaments[_tournamentId];
        newTournament.id = _tournamentId;
        newTournament.users_name = users_name;
        newTournament.exists = true;

        // emit event is used to notify the frontend
        emit TournamentCreated(_tournamentId, users_name);
    }

    // Function to update the score of a user in a tournament
    function updateScore(uint256 _tournamentId, bytes32 _user, uint256 _score) public {
        require(tournaments[_tournamentId].exists, "Tournament does not exist");
        
        Tournament storage tournament = tournaments[_tournamentId];
        require(isUserInTournament(tournament, _user), "User is not in the tournament");

        tournament.scores[_user] = _score;

        emit ScoreUpdated(_tournamentId, _user, _score);
    }

    // Function to get the score of a user in a tournament
    function getScore(uint256 _tournamentId, bytes32 _user) public view returns (uint256) {
        require(tournaments[_tournamentId].exists, "Tournament does not exist");

        Tournament storage tournament = tournaments[_tournamentId];
        require(isUserInTournament(tournament, _user), "User is not in the tournament");

        return tournaments[_tournamentId].scores[_user];
    }

    // Internal function to check if a user is in the tournament
    function isUserInTournament(Tournament storage tournament, bytes32 _user) internal view returns (bool) {
        for (uint256 i = 0; i < tournament.users_name.length; i++) {
            if (tournament.users_name[i] == _user) {
                return true;
            }
        }
        return false;
    }

    // Get tournament winner
    function getWinner(uint256 _tournamentId) public view returns (bytes32) {
        require(tournaments[_tournamentId].exists, "Tournament does not exist");

        Tournament storage tournament = tournaments[_tournamentId];
        require(tournament.users_name.length > 0, "No users in the tournament");

        bytes32 winner = tournament.users_name[0];
        uint256 maxScore = tournament.scores[winner];

        for (uint256 i = 1; i < tournament.users_name.length; i++) {
            uint256 score = tournament.scores[tournament.users_name[i]];
            if (score > maxScore) {
                winner = tournament.users_name[i];
                maxScore = score;
            }
        }

        require(maxScore == 2, "No winner in the tournament");

        return winner;
    }
}
