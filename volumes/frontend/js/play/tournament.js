
function checkValidInputTournament(p1_name, p2_name, p3_name, p4_name) {
  let lang = getCookie('django_language');

  // Check if the names are different
  if (p1_name === p2_name || p1_name === p3_name || p1_name === p4_name ||
    p2_name === p3_name || p2_name === p4_name || p3_name === p4_name) {
    // console.log(
    //   'p1_name: ', p1_name, 'p2_name: ', p2_name, 'p3_name: ', p3_name,
    //   'p4_name: ', p4_name);
    let error = 'Names must be unique';
    // console.log('error: ', error);
    if (lang === 'fr')
      error = 'Les noms doivent être uniques';
    else if (lang === 'es')
      error = 'Los nombres deben ser únicos';
    displayError(error);

    return false;
  }

  let names = [p1_name, p2_name, p3_name, p4_name];
  for (const name of names) {
    // Check if the names are empty or only whitespace
    if (name.length === 0 || name.trim().length === 0) {
      let error = 'Name can\'t be empty';
      // console.log('error: ', error);
      if (lang === 'fr')
        error = 'Le nom ne peut pas être vide';
      else if (lang === 'es')
        error = 'El nombre no puede estar vacío';
      displayError(error);

      return false;
    }

    // Check name length <= 16
    if (name.length > 16) {
      let error = 'Name must be 16 characters or less';
      // console.log('error: ', error);
      if (lang === 'fr')
        error = 'Le nom doit comporter 16 caractères ou moins';
      else if (lang === 'es')
        error = 'El nombre debe tener 16 caracteres o menos';
      displayError(error);

      return false;
    }

    // Check if names are alphanumerical
    if (!/^[a-zA-Z0-9_]+$/.test(name)) {
      let error = 'Names must be alphanumerical';
      // console.log('error: ', error);
      if (lang === 'fr')
        error = 'Les noms doivent être alphanumériques';
      else if (lang === 'es')
        error = 'Los nombres deben ser alfanuméricos';
      displayError(error);

      return false;
    }
  }

  return true;
}

async function playTournament() {
  // console.log('playTournament');
  // gameMode: 'local'
  // gameType: 'pong' or cows
  // gameRound: 'single', 'Semi-Final 1', 'Semi-Final 2', 'Final'

  const p1_name = document.getElementById('player1-input').value;
  const p2_name = document.getElementById('player2-input').value;
  const p3_name = document.getElementById('player3-input').value;
  const p4_name = document.getElementById('player4-input').value;

  const gameType =
    document.querySelector('input[name="chosenGame-tnmt"]:checked').id;

  // console.log(gameType, p1_name, p2_name, p3_name, p4_name);

  // check names are valid
  if (!checkValidInputTournament(p1_name, p2_name, p3_name, p4_name)) return;

  let gameMode = 'local';
  let gameRound = 'Semi-Final 1';

  startNewTournament(
    gameMode, gameType, gameRound, p1_name, p2_name, p3_name, p4_name);
}
