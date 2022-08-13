import estimator.core 

def estimate(width, height, data, player_to_move, trials, tolerance):

  return estimator.core.estimate(width, height, data, player_to_move, trials, tolerance)

estimate.__annotations__ = {
    'width': int, 'height': int, 'data': [], 'player_to_move': int,
    'trials': int, 'tolerance': float, 'return': int,
}