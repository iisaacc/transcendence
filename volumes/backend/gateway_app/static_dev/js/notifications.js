/* -------------------Friend Request notification------------------- */

function removeEmptyMessage() {
  const emptyMessage = document.getElementById('notificationContent');
  if (emptyMessage) {
    if (emptyMessage.innerHTML.trim() === 'You have no notifications' || emptyMessage.innerHTML.trim() === 'No tienes notificaciones' || emptyMessage.innerHTML.trim() === 'Vous n\'avez pas de notifications') {
      // console.log('addRequestNotification > Removing empty message');
      emptyMessage.remove();
      unreadNotifications = false;

    }
    // else {
    //   console.log('addRequestNotification > No empty message to remove');
    //   console.log('addRequestNotification > emptyMessage.innerHTML:', emptyMessage.innerHTML);
    // }

  }
}

function createAvatarElement(avatar_url) {
  const avatar = document.createElement('img');

  avatar.src = avatar_url;
  avatar.alt = 'Avatar';
  avatar.style.height = '3rem';
  avatar.style.width = '3rem';
  avatar.style.objectFit = 'cover';
  avatar.style.borderRadius = '50%';
  avatar.style.marginRight = '10px';
  avatar.style.border = '1px solid white';
  avatar.id = 'avatar';

  return avatar;
}

function createMessageElement(sender_username, response) {
  const message = document.createElement('span');
  message.textContent = `${sender_username} ${response}`;
  //  message.textContent = `${sender_username} sent you a friend request.`;
  message.style.marginLeft = '10px';
  return message;
}

function createDateElement(dateString, newNotification) {
  const date = new Date(dateString);
  const formattedDate = date.toLocaleDateString();
  const formattedTime = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  const formattedDateTime = `${formattedDate} ${formattedTime}`;

  const container = document.createElement('div');
  container.style.display = 'flex';
  container.style.flexDirection = 'column';
  container.style.alignItems = 'center';

  const dateElement = document.createElement('span');
  dateElement.textContent = formattedDateTime;
  dateElement.style.marginRight = '10px';
  dateElement.style.fontSize = '0.8rem';
  dateElement.style.color = 'grey';
  container.appendChild(dateElement);

  newNotification.appendChild(container);

  return dateElement;
}

function appendElements(avatar, message, acceptButton, declineButton, newNotification, status, type) {
  // Style the notification
  newNotification.style.color = 'white';
  newNotification.style.setProperty('--bs-dropdown-link-hover-bg', 'transparent');

  // Set data atribute to identify the notification
  newNotification.setAttribute('data-type', 'friend-invite');
  newNotification.setAttribute('data-userid', sender_id);

  const contentDiv = document.createElement('div');
  contentDiv.style.display = 'flex';
  contentDiv.style.flexDirection = 'row';
  contentDiv.style.justifyContent = 'space-between';
  contentDiv.style.alignItems = 'center';
  contentDiv.style.width = '100%';

  const leftContainer = document.createElement('div');
  leftContainer.style.display = 'flex';
  leftContainer.style.flexDirection = 'row';
  leftContainer.style.alignItems = 'center';

  leftContainer.appendChild(avatar);
  leftContainer.appendChild(message);

  contentDiv.appendChild(leftContainer);

  // Set buttons only if status is pending
  if (status !== 'accepted' && status !== 'declined' && type !== 'block' && type !== 'unblock') {
    const markersDiv = document.createElement('div');
    markersDiv.style.display = 'flex';
    markersDiv.style.flexDirection = 'row';
    markersDiv.style.alignItems = 'center';
    markersDiv.appendChild(acceptButton);
    markersDiv.appendChild(declineButton);
    contentDiv.appendChild(markersDiv);
  }
  newNotification.appendChild(contentDiv);

  // Add a separator
  const separator = document.createElement('hr');
  separator.style.border = '0';
  separator.style.height = '1px';
  separator.style.background = 'grey';
  separator.style.margin = '10px 0'; // Adjust margin as needed

  newNotification.appendChild(separator);

  // Set data attribute to identify the notification
  newNotification.setAttribute('data-type', 'friend-invite');
  newNotification.setAttribute('data-userid', sender_id);
  newNotification.setAttribute('data-targetid', receiver_id);

}

function appendAvatarAndMessage(avatar, message, newNotification) {
  // Style the notification
  newNotification.style.color = 'white';
  newNotification.style.setProperty('--bs-dropdown-link-hover-bg', 'transparent');

  newNotification.appendChild(avatar);
  newNotification.appendChild(message);
  // Set data atribute to identify the notification
  newNotification.setAttribute('data-type', 'friend-invite');
  newNotification.setAttribute('data-userid', sender_id);

  // Add a separator
  const separator = document.createElement('hr');
  separator.style.border = '0';
  separator.style.height = '1px';
  separator.style.background = 'grey';
  separator.style.margin = '10px 0'; // Adjust margin as needed

  newNotification.appendChild(separator);

  // Set data attribute to identify the notification
  newNotification.setAttribute('data-type', 'friend-invite');
  newNotification.setAttribute('data-userid', sender_id);

}

function createAcceptButton(sender_id, receiver_id, newNotification) {
  const acceptButton = document.createElement('img');
  acceptButton.src = '/media/utils_icons/check_73F84A.svg';
  acceptButton.alt = 'Accept';
  acceptButton.style.height = '2rem';
  acceptButton.style.width = '2rem';
  acceptButton.style.objectFit = 'cover';
  acceptButton.style.marginLeft = '10px';
  acceptButton.style.cursor = 'pointer';
  acceptButton.style.backgroundColor = 'transparent';

  //   acceptButton.onclick = function() {
  //     mainRoomSocket.send(JSON.stringify({'type': 'friend_request_response', 'response': 'accept', 'sender_id': sender_id, 'receiver_id': receiver_id}));
  // //    newNotification.remove(); uncomment
  //   }

  return acceptButton;
}

function changeNotificationIconToUp(notificationDropdownClass, newNotification, notificationDropdown, receiver_id, status) {
  // if there is not unread notifications, change the bell icon to down

  if (notificationDropdownClass) {
    //notificationDropdown.insertBefore(newNotification, notificationDropdown.firstChild);
    // console.log('addRequestNotification > notificationDropdown:', notificationDropdown);
    const bellIcon = notificationDropdown.querySelector('img');
    if (bellIcon && status !== 'accepted' && status !== 'declined') {
      // console.log('addRequestNotification > status:', status);
      bellIcon.src = '/media/utils_icons/bell_up.png';
    }
  }
  else {
    console.error('addRequestNotification > notificationDropdown is null');
  }
}

function createDeclineButton(sender_id, receiver_id, newNotification) {
  const declineButton = document.createElement('img');
  declineButton.src = '/media/utils_icons/cancel_EE3324.svg';
  declineButton.alt = 'Decline';
  declineButton.style.height = '2rem';
  declineButton.style.width = '2rem';
  declineButton.style.objectFit = 'cover';
  declineButton.style.marginLeft = '10px';
  declineButton.style.cursor = 'pointer'; // Change cursor to pointer to indicate it's clickable
  declineButton.style.backgroundColor = 'transparent';

  //   declineButton.onclick = function() {
  //     mainRoomSocket.send(JSON.stringify({'type': 'friend_request_response', 'response': 'decline', 'sender_id': sender_id, 'receiver_id': receiver_id}));
  // //    newNotification.remove(); uncomment
  //   }

  // Append the button to the newNotification element

  return declineButton;
}

function listenUserResponse(acceptButton, declineButton, sender_id, receiver_id, sender_username, receiver_username, type, data) {
  // response_type = type + '_response';
  // console.log('listenUserResponse > response_type:', response_type);

  acceptButton.addEventListener('click', async function (event) {
    // console.log('Accept button clicked');

    response_type = type + '_response';

    // Check if a user is blocked
    let blocked, imBlocked;
    if (type === 'game_request') {
      blocked = await checkIfBlocked(sender_id);
      imBlocked = await checkIfImBlocked(sender_id);
    }
    else if (type === 'game_request_response') {
      blocked = await checkIfBlocked(receiver_id);
      imBlocked = await checkIfImBlocked(receiver_id);
    }

    if (blocked || imBlocked) {
      acceptButton.remove();
      declineButton.remove();

      let lang = getCookie('django_language');
      let error = 'You cannot play with this user';
      if (lang === 'fr')
        error = 'Vous ne pouvez pas jouer avec cet utilisateur';
      else if (lang === 'es')
        error = 'No puedes jugar con este usuario';
      displayMessageInModal(error);

      return;
    }

    // Sender is notified that the receiver has accepted the invite
    if (sendMessagesBySocket({
      'type': response_type,
      'response': 'accept',
      'sender_id': sender_id,
      'receiver_id': receiver_id,
      'sender_username': sender_username,
      'receiver_username': receiver_username,
      'game_mode': data.game_mode,
      'game_type': data.game_type,
      'sender_avatar_url': data.sender_avatar_url,
      'receiver_avatar_url': data.receiver_avatar_url
    }, mainRoomSocket) == true) {
      acceptButton.remove();
      declineButton.remove();
    }

    // console.log('listenUserResponse > type:', type, ', data:', data);
    if (type === 'game_request') {
      // Cancel current game if any
      if (calcGameSocket) {
        calcGameSocket.close();
        calcGameSocket = null;
      }
      // Receiver accepts the invite and goes to the waiting room
      playGameInvite(data.game_mode, data.game_type, receiver_username, { sender_username, sender_id, receiver_username, receiver_id });

    }
    else if (type === 'game_request_response') {
      // Cancel current game if any
      if (calcGameSocket) {
        calcGameSocket.close();
        calcGameSocket = null;
      }
      // Sender accepts the invite response and goes to the waiting room
      playGameInvite(data.game_mode, data.game_type, sender_username, { sender_username, sender_id, receiver_username, receiver_id });

    }
    else if (type === 'friend_request') {
      // Sender accepts the friend request response
      updateFriendsState();
    }

  });

  declineButton.addEventListener('click', function () {

    response_type = type + '_response';

    if (sendMessagesBySocket({
      'type': response_type,
      'response': 'decline',
      'sender_id': sender_id,
      'receiver_id': receiver_id,
      'sender_username': sender_username,
      'receiver_username': receiver_username,
      'sender_avatar_url': data.sender_avatar_url,
      'receiver_avatar_url': data.receiver_avatar_url
    }
      , mainRoomSocket) == true) {

      if (type === 'game_request_response') {
        // Sender cancels the invite response. The receiver in the waiting room needs to be notified
        sendMessagesBySocket({
          'type': 'cancel_waiting_room',
          'response': 'decline',
          'sender_id': receiver_id,
          'receiver_id': sender_id,
          'sender_username': receiver_username,
          'receiver_username': sender_username,
          'receiver_avatar_url': data.receiver_avatar_url,
          'sender_avatar_url': data.sender_avatar_url
        }
          , mainRoomSocket);

      }

      acceptButton.remove();
      declineButton.remove();
    }

  });

  // document.addEventListener('DOMContentLoaded', function () {
  //   const notificationDropdown = document.getElementById('navbarDropdownNotifications');
  //   notificationDropdown.addEventListener('click', function () {
  //     unreadNotifications = false;
  //     sendMessagesBySocket({
  //       'type': 'mark_notification_as_read',
  //       'receiver_id': receiver_id,
  //       'sender_id': sender_id
  //     }, mainRoomSocket);
  //   }
  //   );
  // });
}


function deleteResponsesButtonsId(notificationDropdownClass, userid) {
  const notifications = notificationDropdownClass.children;

  for (let i = 0; i < notifications.length; i++) {
    const notification = notifications[i];
    const buttons = notification.querySelectorAll('img');
    // console.log('deleteResponsesButtonsId > notification:', notification);
    // console.log('deleteResponsesButtonsId > buttons:', buttons);

    const targetId = notification.getAttribute('data-targetid');

    if (targetId == userid && buttons.length > 0) {
      // If the image is not the avatar, remove it
      buttons.forEach(button => {
        if (button.id !== 'avatar') {
          button.remove();
        }
      });
    }
  }
}


function addRequestNotification(data) {
  const notificationDropdown = document.getElementById('navbarDropdownNotifications');
  const notificationDropdownClass = document.getElementById('notificationClassContent');
  receiver_username = data.receiver_username;
  receiver_id = data.receiver_id;
  sender_username = data.receiver_username;
  sender_username = data.sender_username;
  sender_id = data.sender_id;
  sender_avatar_url = data.sender_avatar_url;
  type = data.type;
  // example.data = {
  //   date: "2024-10-24 17:49:53"
  //   game_mode: "invite"
  //   game_type: "pong"
  //   message: "code has invited you to play: Pong"
  //   receiver_avatar_url: "/media//avatars/default.png"
  //   receiver_id: 3
  //   receiver_username: "code"
  //   sender_avatar_url: "/media/avatars/default.png"
  //   sender_id: 2
  //   sender_username: "code"
  //   type: "game_request"
  // }

  // Remove the 'no notifications' message
  removeEmptyMessage();

  // Create a new notification element
  const newNotification = document.createElement('li');
  // newNotification.id = sender_username;
  newNotification.classList.add('dropdown-item');
  // style the notification --bs-dropdown-link-active-bg: var(--bs-danger-rgb);
  newNotification.style.setProperty('--bs-dropdown-link-active-bg', 'transparent');
  // Prevents the dropdown from closing
  newNotification.addEventListener('click', function (event) {
    event.stopPropagation();
  });

  // Create an element for the date
  const date = createDateElement(data.date, newNotification);

  // Create an img element for the avatar
  const avatar = createAvatarElement(sender_avatar_url);

  // Create a span element for the message
  const message = createMessageElement(sender_username, friendRequestReceived);
  if (data.type === 'game_request') {
    // message.textContent = `${sender_username} invited you to play a game.`;
    message.textContent = sender_username + gameRequestReceived + data.game_type;
  }
  else if (data.type === 'block') {
    message.textContent = sender_username + ' ' + userBlocked;
  }
  else if (data.type === 'unblock') {
    message.textContent = sender_username + ' ' + userUnblocked;
    // console.log('addRequestNotification > message:', message);
  }

  // Add button to accept the friend request represented by accept png
  const acceptButton = createAcceptButton(sender_id, receiver_id, newNotification);
  // Add button to decline the friend request represented by decline png
  const declineButton = createDeclineButton(sender_id, receiver_id, newNotification);

  // If data type is game, delete the accept and decline buttons from other previous games notifications
  if (data.type === 'game_request')
    deleteResponsesButtonsId(notificationDropdownClass, sender_id);

  // Append the avatar and message to the newNotification element
  appendElements(avatar, message, acceptButton, declineButton, newNotification, data.status, type);

  // Change default down icon notification to the new notification icon if the notif has not been read
  if (data.status !== 'read') {
    changeNotificationIconToUp(notificationDropdownClass, newNotification, notificationDropdown, receiver_id, data.status);
  }

  // Set last notification on top
  if (notificationDropdownClass.childElementCount === 0) {
    notificationDropdownClass.appendChild(newNotification);
  }
  else {
    notificationDropdownClass.insertBefore(newNotification, notificationDropdownClass.firstChild);
  }

  // Set unreadNotifications to true
  unreadNotifications = true;

  // Add event listener to the buttons accept and decline
  listenUserResponse(acceptButton, declineButton, sender_id, receiver_id, sender_username, receiver_username, data.type, data);
}

/* -------------------Friend Response notification------------------- */
function addResponseNotification(data) {
  const notificationDropdown = document.getElementById('navbarDropdownNotifications');
  const notificationDropdownClass = document.getElementById('notificationClassContent');
  receiver_username = data.receiver_username;
  receiver_id = data.receiver_id;
  sender_username = data.sender_username;
  sender_id = data.sender_id;
  receiver_avatar_url = data.receiver_avatar_url;
  sender_avatar_url = data.sender_avatar_url;

  // Remove the 'no notifications' message
  removeEmptyMessage();

  // Create a new notification element
  const newNotification = document.createElement('li');
  newNotification.classList.add('dropdown-item');
  newNotification.style.setProperty('--bs-dropdown-link-active-bg', 'transparent');
  // Prevents the dropdown from closing
  newNotification.addEventListener('click', function (event) {
    event.stopPropagation();
  });

  // Create an element for the date
  const date = createDateElement(data.date, newNotification);

  // Create an img element for the avatar
  // const avatar = createAvatarElement(receiver_avatar_url);
  const avatar = createAvatarElement(receiver_avatar_url);

  // Create a span element for the message
  // console.warn('addResponseNotification > data:', data);
  inputMessage = gameRequestCancelled;
  if (data.type === 'friend_request_response') {
    // if data.message contrains 'accepted', then the message is 'accepted'
    if (data.message.includes('accepted')) {
      inputMessage = friendRequestAccepted;
    }
    else if (data.message.includes('declined')) {
      inputMessage = friendRequestDeclined;
    }
  }
  else if (data.type === 'game_request_response') {
    if (data.message.includes('waiting')) {
      inputMessage = gameRequestAccepted;
    }
    else if (data.message.includes('declined')) {
      inputMessage = gameRequestDeclined;
    }
  }
  else if (data.type === 'cancel_waiting_room' && data.html) {
    inputMessage = gameRequestCancelled;
    document.querySelector('main').innerHTML = data.html;
    displayMessageInModal(data.receiver_username + gameRequestCancelled);
    // console.warn('redirect to home');
  }
  else if (data.type === 'next_in_tournament') {
    inputMessage = gamePlayNextTournament;
  }
  else if (data.type === 'game_request_unconnected') {
    inputMessage = gameRequestUnconnected;
  }

  const message = createMessageElement(receiver_username, inputMessage);
  if (data.response === 'accept' && data.type === 'game_request_response') {
    const acceptButton = createAcceptButton(sender_id, receiver_id, newNotification);

    const declineButton = createDeclineButton(sender_id, receiver_id, newNotification);

    // If data type is game, delete the accept and decline buttons from other previous games notifications
    if (data.type === 'game_request_response' && data.response === 'accept')
      deleteResponsesButtonsId(notificationDropdownClass, receiver_id);

    appendElements(avatar, message, acceptButton, declineButton, newNotification, data.status, data.type);

    // Add event listener to the buttons accept and decline
    listenUserResponse(acceptButton, declineButton, sender_id, receiver_id, sender_username, receiver_username, data.type, data);
  }
  else
    appendAvatarAndMessage(avatar, message, newNotification);

  // Change default down icon notification to the new notification icon
  if (data.status !== 'read') {
    changeNotificationIconToUp(notificationDropdownClass, newNotification, notificationDropdown, receiver_id, data.status);
  }

  // Set last notification on top
  if (notificationDropdownClass.childElementCount === 0) {
    notificationDropdownClass.appendChild(newNotification);
  }
  else {
    notificationDropdownClass.insertBefore(newNotification, notificationDropdownClass.firstChild);
  }

  // Set unreadNotifications to true
  unreadNotifications = true;

}