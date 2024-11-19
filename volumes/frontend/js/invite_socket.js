/* ----------INVITE FRIEND SEARCH */
// The file aim is to handle the search for friends to invite

// Make the websocket accessible globally
let inviteFriendSocket;
//Boolean to check if the input field is focused
isFocused = false;

function sendFriendRequest(sender_username, sender_id, sender_avatar_url, receiver_username, receiver_id) {
  // console.log('sendFriendRequest > sender_username:', sender_username);
  // console.log('sendFriendRequest > sender_id:', sender_avatar_url);
  // console.log('sendFriendRequest > sender_avatar_url:', sender_avatar_url);
  // console.log('sendFriendRequest > receiver_username:', receiver_username);
  // console.log('sendFriendRequest > receiver_id:', receiver_id);
  sendMessagesBySocket({
    'type': 'friend_request',
    'sender_username': sender_username,
    'sender_id': sender_id,
    'sender_avatar_url': sender_avatar_url,
    'receiver_username': receiver_username,
    'receiver_id': receiver_id
  }, mainRoomSocket);
  //  mainRoomSocket.send(JSON.stringify({'type': 'friend_request', 'sender_username': sender_username, 'sender_id': sender_id, 'sender_avatar_url': sender_avatar_url, 'receiver_username': receiver_username, 'receiver_id': receiver_id}));
}

//--------------------------------------------------------------//

// Function to get the CSRF token
function listenSubmit(form) {
  // console.log('form: ', form);
  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    // Ensure modal is closed
    const modal = document.getElementById('inviteFriendModal');
    const modalInstance = bootstrap.Modal.getInstance(modal);
    modalInstance.hide();

    // console.log('Form submitted', e);
    const formData = new FormData(form);
    let url = form.action;

    try {
      // Create a new request for file upload
      let request = new Request(url, {
        method: 'POST',
        headers: {
          'X-Requested-With': 'XMLHttpRequest',  // To identify as AJAX request
          'X-CSRFToken': getCookie('csrftoken')  // If CSRF token is required
        },
        credentials: 'include',  // Include cookies (if necessary)
        body: formData           // FormData handles the file and other fields
        // automatically
      });

      // Send the request and wait a response
      const response = await fetch(request);
      const data = await response.json();
      // console.log('handleFormSubmission > data.message: ', data.message);
      // console.log('handleFormSubmission > response: ', response);


      if (!response.ok) {
        console.error('HTTP error - status:', response.status);
        throw new Error(`HTTP error - status: ${response.status}`);
      }

      // if (data.message === 'Invitation already sent') {
      //   window.location.reload();
      // }

      if (!data?.html?.includes('class="errorlist nonfield')) {
        displayMessageInModal(data.message);
        // console.log('handleFormSubmission > data: ', data);
        if (data.message === 'Invitation sent!' || data.message === '¡Invitación enviada!' || data.message === 'Invitation envoyée !') {
          //console.warn('Send invitation to ', data.username);
          // send invitation to the user
          sendFriendRequest(data.sender_username, data.sender_id, data.sender_avatar_url,
            data.receiver_username, data.receiver_id
          );
        }

      }
      // console.log('handleFormSubmission > data: ', data);
      handleFormSubmission();

    } catch (error) {
      console.error('Form submission error:', error);
      document.querySelector('main').innerHTML =
        '<h1>Form submission error</h1>';
    }
  });
}

// Function to upate the dropdown with matching usernames
function update_dropdown(matching_usernames) {
  const usernameInput = document.getElementById('usernameInput');
  const dropdown = document.getElementById('suggestions-list');  // The dropdown element (create this in HTML)

  // Clear any previous suggestions
  dropdown.innerHTML = '';

  if (matching_usernames.length === 0) {
    //dropdown.classList.remove('show');
    dropdown.style.display = 'none';
    return;
  }

  // Dropdown styling
  dropdown.style.display = 'block';
  dropdown.style.overflowY = 'auto';
  dropdown.style.overflowX = 'hidden';
  dropdown.style.maxHeight = '200px';
  dropdown.style.border = '4px solid #fff';


  // Create a suggestion item for each matching username
  matching_usernames.forEach(username => {
    const suggestionItem = document.createElement('div');
    suggestionItem.classList.add('suggestion-item');
    suggestionItem.textContent = username;

    // Click handler to fill the input field with the selected suggestion
    if (!suggestionItem.hasEventListener) {
      suggestionItem.addEventListener('click', () => {
        usernameInput.value = username;
        dropdown.style.display = 'none';

        //Click on submit button
        const submitButton = document.getElementById('submit-invite-friend');
        if (submitButton) {
          submitButton.click();
        }
      });
      suggestionItem.hasEventListener = true;
    }

    // Append the suggestion item to the dropdown
    dropdown.appendChild(suggestionItem);
  });

  // Close the dropdown when clicking outside
  if (!document.hasEventListener) {
    document.addEventListener('click', (event) => {
      if (!dropdown.contains(event.target) && event.target !== usernameInput) {
        dropdown.style.display = 'none';
      }
    });
    document.hasEventListener = true;
  }
}

// We open the websocket only when the modal is open
function onModalOpen(userID, modal) {
  // console.log('Modal is open');

  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const hostname = window.location.hostname;
  const port = window.location.port ? `:${window.location.port}` : '';
  /* WebSocket */
  inviteFriendSocket = new WebSocket(`${protocol}//${hostname}${port}/wss/inviteafriend/`);

  inviteFriendSocket.onopen = function (e) {
    // console.log('inviteFriendSocket socket connected');
    //    inviteFriendSocket.send(JSON.stringify({type: 'start', 'userID': userID}));
    sendMessagesBySocket({ type: 'start', 'userID': userID }, inviteFriendSocket);
  };

  inviteFriendSocket.onmessage = function (e) {
    const data = JSON.parse(e.data);
    const message = data['message'];
    const type = data['type'];
    // console.log('Received message from socket: ', message);

    if (type === 'suggestions') {
      matching_usernames = data['suggestions'];
      // console.log('Matching usernames:', matching_usernames);
      update_dropdown(matching_usernames);
    }
  };

  inviteFriendSocket.onclose = function (e) {
//    console.warn('inviteFriendSocket socket closed');
  };

  // Listen for modal close
  if (!modal.hasClosingListener) {
  modal.addEventListener('hidden.bs.modal', () => {
    onModalClose(modal);
  });
  modal.hasClosingListener = true;
  }
}

function onModalClose(modal) {
  const formInviteFriend = document.getElementById('type-invite-friend');
  // console.log('Modal is closed');

  // Reset the form
  if (formInviteFriend) {
    formInviteFriend.reset();
    // console.log('Invite Friend form has been reset');
  }

  // Close properly the websocket
  if (inviteFriendSocket ) {
    inviteFriendSocket.close();
    // console.log('Modal is closed and WebSocket is closed');
  } else {
    console.error('inviteFriendWebSocket is not open or already closed');
    // Ensure modal is closed
    const modal = document.getElementById('inviteFriendModal');
    const modalInstance = bootstrap.Modal.getInstance(modal);
    modalInstance.hide();
  }

}

// Function to listen for the friend invitation
async function listenFriendInvitation(modal, form) {
  let inputField = document.getElementById('usernameInput');
  let userID = await getUserID();

  // console.log('User ID:', userID);
  if (userID === '' || userID === undefined) {
    console.error('User ID is not defined');
    // exit ===> handle error
  }

  // Listen for modal open
  if (!modal.hasOpeningListener) {
    modal.addEventListener('show.bs.modal', () => {
      onModalOpen(userID, modal);
    });
    modal.hasOpeningListener = true;
  }
  // Listen for focus on the input field
  if (inputField) {
    if (!inputField.hasFocusListener) {
      inputField.addEventListener('focus', () => {
        isFocused = true;  // Mark input as focused
      });
      inputField.hasFocusListener = true;
    }
    // Listen for blur (when user leaves the input field)
    if (!inputField.hasBlurListener) {
      inputField.addEventListener('blur', () => {
        isFocused = false;  // Mark input as not focused
      });
      inputField.hasBlurListener = true;
    }
  }

  // Event listen for key press
  // console.log('inputField.addEventListene:');
  if (!window.hasKeydownListener) {
    window.addEventListener('keydown', (e) => {

      // get the key pressed
      if (isFocused && inviteFriendSocket.readyState === WebSocket.OPEN) {
        const pressedKey = e.key;
        //      inviteFriendSocket.send(JSON.stringify({type: 'input', 'key': pressedKey}));
        sendMessagesBySocket({ type: 'input', 'key': pressedKey }, inviteFriendSocket);
      }
    });
    window.hasKeydownListener = true;
  }

  // Listen for form submission
  if (form && !form.hasEventListener) {
    // console.log('form has no event listener');
    listenSubmit(form);
    form.hasEventListener = true;
  }
}

function inviteFriendToPlay(sender_username, sender_id, sender_avatar_url, receiver_id, game_type, game_mode) {
  // console.log('inviteFriendToPlay > sender_username:', sender_username, 'sender_id:', sender_id, 'sender_avatar_url:', sender_avatar_url, 'receiver_id:', receiver_id, 'game_type:', game_type, 'game_mode:', game_mode);

  sendMessagesBySocket({
    'type': 'invite_game',
    'sender_username': sender_username,
    'sender_id': sender_id,
    'sender_avatar_url': sender_avatar_url,
    'receiver_id': receiver_id,
    'game_type': game_type,
    'game_mode': game_mode,
  }
    , mainRoomSocket);
}