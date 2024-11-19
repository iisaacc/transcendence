function displayError(errorMessage) {
  const errorDiv = document.getElementById('error-div');
  if (errorDiv) {
    errorDiv.style.display = 'block';
    document.querySelector('.errorlist').textContent = errorMessage;
  }
}

function checkValidInputGame(gameMode, gameType, p1_name, p2_name) {
  let lang = getCookie('django_language');

  // Check if the gameMode and gameType are valid
  if (!gameMode || !gameType ||
    (gameMode !== 'local' && gameMode !== 'remote') ||
    (gameType !== 'pong' && gameType !== 'cows')) {
    let error = 'Invalid selection';
    // console.log('gameMode: ', gameMode, ', gameType: ', gameType);
    if (lang === 'fr')
      error = 'Sélection invalide';
    else if (lang === 'es')
      error = 'Selección inválida';
    displayError(error);

    return false;
  }

  // Check if the names are empty or only whitespace
  if ((p1_name.length === 0 || p1_name.trim().length === 0) ||
    (gameMode === 'local' &&
      (p2_name.length === 0 || p2_name.trim().length === 0))) {
    let error = 'Name can\'t be empty';
    if (lang === 'fr')
      error = 'Le nom ne peut pas être vide';
    else if (lang === 'es')
      error = 'El nombre no puede estar vacío';
    displayError(error);

    return false;
  }

  // Check if the names are different
  if (gameMode === 'local' && (p1_name === p2_name)) {
    let error = 'Names must be different';
    if (lang === 'fr')
      error = 'Les noms doivent être différents';
    else if (lang === 'es')
      error = 'Los nombres deben ser diferentes';
    displayError(error);

    return false;
  }

  // Check name length <= 16
  if (p1_name.length > 16 || (gameMode === 'local' && p2_name.length > 16)) {
    let error = 'Name must be 16 characters or less';
    if (lang === 'fr')
      error = 'Le nom doit comporter 16 caractères ou moins';
    else if (lang === 'es')
      error = 'El nombre debe tener 16 caracteres o menos';
    displayError(error);

    return false;
  }

  // Check if names are alphanumerical
  if (!/^[a-zA-Z0-9_]+$/i.test(p1_name) ||
    (gameMode === 'local' && !/^[a-zA-Z0-9_]+$/i.test(p2_name))) {
    let error = 'Names must be alphanumerical';
    if (lang === 'fr')
      error = 'Les noms doivent être alphanumériques';
    else if (lang === 'es')
      error = 'Los nombres deben ser alfanuméricos';
    displayError(error);

    return false;
  }

  return true;
}

async function checkNameAlreadyExists(name) {
  jsonObject = { 'name': name };

  let path = window.location.pathname;
  let url = '';
  // console.log('path: ', path);
  if (path === '/play/') {
    url = 'checkNameExists/';
  } else if (path === '/play') {
    url = path + '/checkNameExists/';
  }

  try {
    let request = new Request(url, {
      method: 'POST',
      headers: {
        'X-Requested-With': 'XMLHttpRequest',
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken')
      },
      credentials: 'include',
      body: JSON.stringify(jsonObject)
    });

    const response = await fetch(request);
    // console.log(response);

    if (!response.ok) {
      throw new Error(`HTTP error - status: ${response.status}`);
    }
    const data = await response.json();
    // console.log(data);

    if (data.status === 'failure') {
      let lang = getCookie('django_language');
      let error = 'Name not available';
      if (lang === 'fr')
        error = 'Ce nom n\'est pas disponible';
      else if (lang === 'es')
        error = 'Este nombre no está disponible';
      displayError(error);
      return true;
    }

  } catch (error) {
    console.error('Error loading content:', error);
    document.querySelector('main').innerHTML = '<h1>Error loading content</h1>';
    return true;
  }

  return false;
}

// Toggles what's displayed depending on the game mode
function toggleGameMode() {
  const remoteMode = document.getElementById('remoteMode').checked;
  const player2Container = document.getElementById('form-player2');
  const player2Input = document.getElementById('player2-input');
  const playGameButton = document.getElementById('play-game-button');
  const findRemoteButton = document.getElementById('find-remote-button');

  if (remoteMode) {
    player2Container.style.display = 'none';
    player2Input.required = false;
    findRemoteButton.style.display = 'block';
    playGameButton.style.display = 'none';
  } else {
    player2Container.style.display = 'block';
    player2Input.required = true;
    findRemoteButton.style.display = 'none';
    playGameButton.style.display = 'block';
  }
}


// Called from button on Play page, starts a new game
async function playGame() {
  // gameMode: 'local' or 'remote'
  // gameType: 'pong' or 'cows'

  let gameMode = document.querySelector('input[name="gameMode"]:checked').id;
  if (gameMode === 'localMode') gameMode = 'local';
  if (gameMode === 'remoteMode') gameMode = 'remote';

  const gameType =
    document.querySelector('input[name="chosenGame-play"]:checked').id;

  const p1_name = document.getElementById('player1-input').value;
  let p2_name = '';
  if (gameMode === 'local') {
    p2_name = document.getElementById('player2-input').value;
  }

  // check input selection
  if (checkValidInputGame(gameMode, gameType, p1_name, p2_name) == false) return;

  if (gameMode === 'remote') {
    let nameExists = await checkNameAlreadyExists(p1_name);
    if (nameExists)
      return
  }

  // gameRound: 'single', 'Semi-Final 1', 'Semi-Final 2', 'Final'
  const gameRound = 'single';
  const invite_data = {};

  startNewGame(gameMode, gameType, gameRound, p1_name, p2_name, invite_data);
}

// Called from invite notification, starts a new game
async function playGameInvite(gameMode, gameType, p1_name, invite_data) {
  // gameMode: 'invite'
  // gameType: 'pong' or 'cows'

  // const invite_data = {
  //   sender_id,
  //   sender_username,
  //   receiver_id,
  //   receiver_username,
  // };

  let p2_name = '';

  // gameRound: 'single'
  const gameRound = 'single';

  // console.log('playGameInvite > invite_data: ', invite_data, '. This user is p1_name: ', p1_name, ', gameMode: ', gameMode, ', gameType: ', gameType);

  startNewGame(gameMode, gameType, gameRound, p1_name, p2_name, invite_data);
}
