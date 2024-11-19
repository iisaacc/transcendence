// Open WebSocket connection to calcgame and start a new tournament
async function startNewTournament(
  gameMode, gameType, gameRound, p1_name, p2_name, p3_name, p4_name) {

  let cfg;
  let game_id;
  let player_role;

  // Open websocket connection
  calcGameSocket = getCalcGameSocket(gameMode, gameType, gameRound);
  if (calcGameSocket === undefined) return;


  calcGameSocket.onopen = function (e) {
    // console.log('startNewTournament > .onopen, connection opened.');

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
        p3_name: p3_name,
        p4_name: p4_name,
        game_type: gameType,
        game_round: gameRound
      }));

  };

  calcGameSocket.onmessage = function (e) {
    let data = JSON.parse(e.data);

    if (data.type === 'connection_established, calcgame says hello') {
      // console.log(
      //   'startNewTournament > .onmessage connection_established:', data.message);
      cfg = getInitialVariables(gameType, data.initial_vars);

    }  // displays Start button in local and checkboxes in remote
    else if (data.type === 'game_start') {
      // console.log('startNewTournament > .onmessage game_start:', data.message);
      // Load start game page
      document.querySelector('main').innerHTML = data.html;
      if (gameMode === 'local') {
        addStartButtonListener()
      }
      if (gameRound == 'Semi-Final 1') { // start of tournament
        announceGame(data.info.game_round_title,
          `${data.info.p1_name} vs ${data.info.p2_name}`);

        // Send notification, player is next in tournament
        let user_id = (data.info.p1_id != 0) ? data.info.p1_id : data.info.p2_id;
        let username = (data.info.p1_id != 0) ? data.info.p1_name : data.info.p2_name;
        sendMessagesBySocket({ 'type': 'next_in_tournament', 'response': '', 'sender_id': user_id, 'receiver_id': user_id, 'sender_username': username, 'receiver_username': username, 'notify_player': data.info.notify_player }, mainRoomSocket);
      }
      displayKeyUsageInstructions(gameMode, gameType, player_role);

    } else if (data.type === 'game_countdown') {
      // console.log('startNewTournament > .onmessage game_countdown:', data.message);
      if (data.countdown === 3) displayCanvasElement(cfg);
      showCountdown(cfg, data.game_state, data.countdown);

    } else if (data.type === 'game_update') {
      // console.log('startNewTournament > .onmessage game_update:', data.message);
      if (gameType === 'pong')
        renderPongGame(cfg, data.game_state);
      else if (gameType === 'cows')
        renderCowsGame(cfg, data.game_state);

    } else if (data.type === 'game_end') {
      // console.log('startNewTournament > .onmessage game_end:', data.message);
      // console.log('game_result:', data.game_result);

      document.querySelector('#game-container').innerHTML = data.html;
      document.querySelector('#game-container').classList.replace('justify-content-around', 'justify-content-center');
      document.querySelector('.scorePlayer1').textContent =
        data.game_result.p1_score;
      document.querySelector('.scorePlayer2').textContent =
        data.game_result.p2_score;

      if (gameRound != 'single') {
        // console.log('game_end gameRound:', gameRound);
        // console.log('data.info:', data.info);
        addNextRoundButtonListener(data.info);
      }

    } else if (data.type === 'tournament_end') {
      // console.log('startNewTournament > .onmessage tournament_end:', data.message);
      document.querySelector('main').innerHTML = data.html;
      calcGameSocket.close();

      // } else {
      //   console.log('startNewTournament > .onmessage data:', data);
    }
  };

  calcGameSocket.onclose = function (e) {
    // if (!e.wasClean) {
    //   console.error('WebSocket closed unexpectedly:', e);
    // } else {
    //   console.log('startNewTournament > .onclose, connection closed');
    // }

    window.removeEventListener('keydown', handleKeyDown);
    window.removeEventListener('keyup', handleKeyUp);
  };

  // calcGameSocket.onerror = function (e) {
  //   console.error('startNewTournament > .onerror, error occurred: ', e);
  // };

  // Event listeners for controls
  function handleKeyDown(e) {
    if (e.key in cfg.keys) {
      cfg.keys[e.key] = true;
      notifyKeyPressed();
    }
  }

  function handleKeyUp(e) {
    if (e.key in cfg.keys) {
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
    const button = document.getElementById('startGame-button');
    if (button) {
      button.addEventListener('click', () => {
        // console.log('addStartButtonListener > button clicked');
        button.removeEventListener('click', arguments.callee);
        // console.log('addStartButtonListener > removeEventListener');
        calcGameSocket.send(JSON.stringify({ type: 'players_ready' }));
      });
    }
  }
  // Event listener for next round button
  function addNextRoundButtonListener(info) {
    const button = document.getElementById('nextRound-button');
    // console.log('addNextRoundButtonListener > info:', info);
    if (button) {
      button.addEventListener('click', () => {
        // console.log('addNextRoundButtonListener > button clicked');
        button.removeEventListener('click', arguments.callee);
        // console.log('addNextRoundButtonListener > removeEventListener');

        calcGameSocket.send(JSON.stringify({
          type: 'next_game, game details',
          p1_name: info.p1_name,
          p2_name: info.p2_name,
        }));

        announceGame(info.game_round_title,
          `${info.p1_name} vs ${info.p2_name}`);

        document.querySelector('h1').textContent = info.game_round_title;
        document.getElementById('namePlayer1').textContent = info.p1_name;
        document.getElementById('namePlayer2').textContent = info.p2_name;
        document.querySelector('.scorePlayer1').textContent = '0';
        document.querySelector('.scorePlayer2').textContent = '0';

        document.getElementById('nextRound-button').style.display = 'none';
        document.getElementById('startGame-winner').style.display = 'none';
        document.getElementById('startGame-button').style.display = 'block';

        document.getElementById('photoPlayer1').src = origin + '/static/images/face_48.svg';
        document.getElementById('photoPlayer2').src = origin + '/static/images/face_48.svg';
        if (info.p1_avatar_url)
          document.getElementById('photoPlayer1').src = origin + '/media' + info.p1_avatar_url;
        else if (info.p2_avatar_url)
          document.getElementById('photoPlayer2').src = origin + '/media' + info.p2_avatar_url;

        // Send notification, player is next in tournament
        let user_id = (info.p1_id != 0) ? info.p1_id : info.p2_id;
        let username = (info.p1_id != 0) ? info.p1_name : info.p2_name;
        sendMessagesBySocket({ 'type': 'next_in_tournament', 'response': '', 'sender_id': user_id, 'receiver_id': user_id, 'sender_username': username, 'receiver_username': username, 'notify_player': info.notify_player }, mainRoomSocket);

        addStartButtonListener();

      });
    }
  }
}
