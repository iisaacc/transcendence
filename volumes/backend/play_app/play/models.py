from django.db import models
import logging, random
logger = logging.getLogger(__name__)

# Game model with 2 players, score and winner
class Game(models.Model):
    GAME_TYPES = [
        ('pong', 'pong'),
        ('cows', 'cows'),
    ]

    GAME_ROUNDS = [
        ('single', 'single'),
        ('semifinal1', 'Semi-Final 1'),
        ('semifinal2', 'Semi-Final 2'),
        ('final', 'Final'),
    ]

    game_type = models.CharField(max_length=16, choices=GAME_TYPES)
    game_round = models.CharField(max_length=16, choices=GAME_ROUNDS, default='single')

    # player1 = models.ForeignKey(Player, related_name='player1_games', on_delete=models.SET_NULL, null=True)
    # player2 = models.ForeignKey(Player, related_name='player2_games', on_delete=models.SET_NULL, null=True)    

    p1_id = models.IntegerField()
    p1_name = models.CharField(max_length=16)

    p2_id = models.IntegerField()
    p2_name = models.CharField(max_length=16)

    p1_score = models.IntegerField()
    p2_score = models.IntegerField()

    game_winner_name = models.CharField(max_length=16, null=True, blank=True)
    game_winner_id = models.IntegerField(null=True, blank=True)

    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.game_type}: {self.p1_name} ({self.p1_score}) vs {self.p2_name} ({self.p2_score})"

# Tournament with 4 players, 2 semi-finals, final and winner
class Tournament(models.Model):
    GAME_TYPES = [
        ('pong', 'pong'),
        ('cows', 'cows'),
    ]
    game_type = models.CharField(max_length=16, choices=GAME_TYPES)

    # Player Information
    t_p1_id = models.IntegerField()
    t_p1_name = models.CharField(max_length=16)
    
    t_p2_id = models.IntegerField()
    t_p2_name = models.CharField(max_length=16)
    
    t_p3_id = models.IntegerField()
    t_p3_name = models.CharField(max_length=16)
    
    t_p4_id = models.IntegerField()
    t_p4_name = models.CharField(max_length=16)
    
    # Game Relationships
    semifinal1 = models.ForeignKey(Game, on_delete=models.SET_NULL, null=True, blank=True, related_name='tournament_semifinal1')
    semifinal2 = models.ForeignKey(Game, on_delete=models.SET_NULL, null=True, blank=True, related_name='tournament_semifinal2')
    final = models.ForeignKey(Game, on_delete=models.SET_NULL, null=True, blank=True, related_name='tournament_final')

    t_winner_id = models.IntegerField(null=True, blank=True)
    t_winner_name = models.CharField(max_length=16, null=True, blank=True)
    
    date_started = models.DateTimeField(auto_now_add=True)
    date_finished = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Tournament {self.id}"

    def start_tournament(self):
        # Create the two semi-final games
        logger.debug('class Tournament > start_tournament')
        if not self.semifinal1 and not self.semifinal2:
            logger.debug('class Tournament > start_tournament > Create semi-final games')

            players = [
                {'id': self.t_p1_id, 'name': self.t_p1_name},
                {'id': self.t_p2_id, 'name': self.t_p2_name},
                {'id': self.t_p3_id, 'name': self.t_p3_name},
                {'id': self.t_p4_id, 'name': self.t_p4_name},
            ]
            logger.debug(f'Players: {players}')
            random.shuffle(players)
            logger.debug(f'Players: {players}')
            
            self.semifinal1 = Game.objects.create(
                game_type=self.game_type,
                game_round='semifinal1',
                p1_id=players[0]['id'], p1_name=players[0]['name'],
                p2_id=players[1]['id'], p2_name=players[1]['name'],
                p1_score=0, p2_score=0
            )
            self.semifinal2 = Game.objects.create(
                game_type=self.game_type,
                game_round='semifinal2',
                p1_id=players[2]['id'], p1_name=players[2]['name'],
                p2_id=players[3]['id'], p2_name=players[3]['name'],
                p1_score=0, p2_score=0
            )

            self.save()

    def create_final(self):
        # Create the final game
        logger.debug('class Tournament > create_final')
        if not self.final:
            self.final = Game.objects.create(
                game_type=self.game_type,
                game_round='final',
                p1_id=self.semifinal1.game_winner_id, p1_name=self.semifinal1.game_winner_name,
                p2_id=self.semifinal2.game_winner_id, p2_name=self.semifinal2.game_winner_name,
                p1_score=0, p2_score=0
            )
            self.save()
