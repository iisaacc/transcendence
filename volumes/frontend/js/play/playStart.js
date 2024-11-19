let calcGameSocket;

// Open WebSocket connection to calcgame and start a new local or remote game
async function startNewGame(gameMode, gameType, gameRound, p1_name, p2_name, invite_data) {

  let cfg;
  let game_id;
  let player_role;

  // Open websocket connection
  calcGameSocket = getCalcGameSocket(gameMode, gameType, gameRound);
  if (calcGameSocket === undefined) return;

  calcGameSocket.onopen = function (e) {
    // console.log('startNewGame > .onopen, connection opened.');

    // Set up event listeners on navbar items to close connection on navigate
    setupNavbarNavigateEventListeners(calcGameSocket);
    // Set up event listeners for controls
    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);

    if (gameMode === 'local')
      calcGameSocket.send(JSON.stringify({
        type: 'opening_connection, game details',
        p1_name: p1_name,
        p2_name: p2_name,
        game_type: gameType
      }));

    else if (gameMode === 'remote')
      calcGameSocket.send(JSON.stringify({
        type: 'opening_connection, my name is',
        p1_name: p1_name,
        game_type: gameType
      }));

    else if (gameMode === 'invite')
      calcGameSocket.send(JSON.stringify({
        type: 'opening_connection, invite',
        p1_name: p1_name,
        sender_name: invite_data.sender_username,
        sender_id: invite_data.sender_id,
        receiver_name: invite_data.receiver_username,
        receiver_id: invite_data.receiver_id,
        game_type: gameType
      }));
  };

  calcGameSocket.onmessage = function (e) {
    let data = JSON.parse(e.data);

    if (data.type === 'connection_established, calcgame says hello') {
      // console.log(
      //   'startNewGame > .onmessage connection_established:', data.message);
      cfg = getInitialVariables(gameType, data.initial_vars);

    } else if (data.type === 'already_in_game') {  // while finding an opponent
      // in remote
      // console.log('startNewGame > .onmessage already_in_game:', data.message);
      // Load html waiting room
      document.querySelector('main').innerHTML = data.html;
      announceGame(data.title, data.message);

    } else if (data.type === 'blocked_user') {
      // console.warn('startNewGame > .onmessage blocked_user:', data.type);

      document.querySelector('main').innerHTML = data.html;
      announceGame(data.title, data.message);
      calcGameSocket.close();

    } else if (data.type === 'waiting_room') {  // while finding an opponent
      // in remote
      // console.log('startNewGame > .onmessage waiting_room:', data.message);
      // Load html waiting room
      document.querySelector('main').innerHTML = data.html;

    }  // displays Start button in local and checkboxes in remote
    else if (data.type === 'game_start') {
      // console.log('startNewGame > .onmessage game_start:', data.message);
      // Load start game page
      document.querySelector('main').innerHTML = data.html;
      if (gameMode === 'local') {
        addStartButtonListener()
      } else if (gameMode === 'remote' || gameMode === 'invite') {
        game_id = data.game_id;
        player_role = data.player_role;
        addIndicatorToThisPlayer(player_role);
        announceGame(data.title, data.message);
        setPlayerReadyCheckBoxes(player_role, calcGameSocket, game_id);
      }
      displayKeyUsageInstructions(gameMode, gameType, player_role);

    }  // updates oppenent's ready checkbox in remote
    else if (data.type === 'opponent_ready') {
      // console.log('startNewGame > .onmessage opponent_ready:', data.message);
      updateOpponentReadyCheckBoxes(data.opponent)

    } else if (data.type === 'game_countdown') {
      // console.log('startNewGame > .onmessage game_countdown:', data.message);
      if (data.countdown === 3) displayCanvasElement(cfg);
      showCountdown(cfg, data.game_state, data.countdown);

    } else if (data.type === 'game_update') {
      // console.log('startNewGame > .onmessage game_update:', data.message);
      if (gameType === 'pong')
        renderPongGame(cfg, data.game_state);
      else if (gameType === 'cows')
        renderCowsGame(cfg, data.game_state);

    } else if (data.type === 'game_end') {
      // console.log('startNewGame > .onmessage game_end:', data.message);
      // console.log('game_result:', data.game_result);
      // console.log('game_end data:', data);

      document.querySelector('#game-container').innerHTML = data.html;
      document.querySelector('#game-container').classList.replace('justify-content-around', 'justify-content-center');
      document.querySelector('.scorePlayer1').textContent =
        data.game_result.p1_score;
      document.querySelector('.scorePlayer2').textContent =
        data.game_result.p2_score;

      calcGameSocket.close();

    } else if (data.type === 'disconnection') {
      // console.log('startNewGame > .onmessage disconnection:', data.message);
      // console.log('game_result:', data.game_result);
      // console.log('disconnection data:', data);

      document.querySelector('#game-container').innerHTML = data.html;
      document.querySelector('#game-container').classList.replace('justify-content-around', 'justify-content-center');
      document.querySelector('.scorePlayer1').textContent =
        data.game_result.p1_score;
      document.querySelector('.scorePlayer2').textContent =
        data.game_result.p2_score;
      announceGame(data.title, data.message);

      calcGameSocket.close();

      // } else {
      // console.log('startNewGame > .onmessage data:', data);
    }
  };

  calcGameSocket.onclose = function (e) {
    // if (!e.wasClean) {
    //   console.error('WebSocket closed unexpectedly:', e);
    // } else {
    //   console.log('startNewGame > .onclose, connection closed');
    // }

    window.removeEventListener('keydown', handleKeyDown);
    window.removeEventListener('keyup', handleKeyUp);
  };

  // calcGameSocket.onerror = function (e) {
  //   console.error('startNewGame > .onerror, error occurred: ', e);
  // };

  // Event listeners for controls
  function handleKeyDown(e) {
    if (cfg.keys && e.key in cfg.keys) {
      cfg.keys[e.key] = true;
      notifyKeyPressed();
    }
  }

  function handleKeyUp(e) {
    if (cfg.keys && e.key in cfg.keys) {
      cfg.keys[e.key] = false;
      notifyKeyPressed();
    }
  }

  function notifyKeyPressed() {
    // Filter out the keys that are pressed
    const pressedKeys = Object.keys(cfg.keys).filter(key => cfg.keys[key]);
    calcGameSocket.send(JSON.stringify(
      { type: 'key_press', keys: pressedKeys, game_id, player_role }));
  }

  // Event listener for start button
  function addStartButtonListener() {
    const startButton = document.getElementById('startGame-button');
    if (startButton) {
      startButton.addEventListener('click', () => {
        startButton.removeEventListener('click', arguments.callee);
        calcGameSocket.send(JSON.stringify({ type: 'players_ready' }));
      });
    }
  }
}
