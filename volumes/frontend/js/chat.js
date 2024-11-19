async function init_listening() {

  // const stackTrace = new Error().stack;
  // console.log('init_listening call stack:', stackTrace);

  let friendsData = [];
  const userID = g_user_id;
  if (userID === 0 || userID === '0' || userID === '' || userID === undefined || userID === null || userID === 'None' || userID === '[object HTMLInputElement]') {
    console.error('Client is not logged in, cannot use websocket');
    return;
  }
  const chatButton = document.getElementById('chatButton');
  const messageInput = document.getElementById('messageInput');
  const sendButton = document.getElementById('sendButton');
  const chatModal = document.getElementById('chatModal');

  if (chatModal) {
    chatModal.addEventListener('hidden.bs.modal', () => {
      // console.log('Chat modal is closed');
      const currentChatId = document.getElementById('currentChatId');
      currentChatId.value = '';
    });
  }

  // console.log('chat.js > chatButton:', chatButton);
  // Listen for the chat button click
  chatButton?.addEventListener('click', async () => {
    friendsData = await getFriendsData();
    displayFriendsInChat(friendsData);
  });

  // Send message
  function sendChatMessage() {
    const selectedContact = document.querySelector('.list-group-item.selected-contact');
    const blockSwitch = document.querySelector('input[data-user-id]');

    if (!selectedContact) {
      // messageInput.placeholder = 'Select a contact to send a message';
      // console.log('No contact selected');
      return;
    } else if (!messageInput.value) {
      // messageInput.placeholder = 'Type a message to send';
      // console.log('No message to send');
      return;
    } else if (blockSwitch.checked) {
      // messageInput.placeholder = 'You cannot send messages to blocked users';
      // console.log('Cannot send messages to blocked users');
      return;
    } else if (messageInput.value.length > 1000) {
      let lang = getCookie('django_language');
      let error = 'Message too long, max 1000';
      if (lang === 'fr')
        error = 'Message trop long, max 1000';
      else if (lang === 'es')
        error = 'Mensaje demasiado largo, máximo 1000';
      messageInput.value = '';
      alert(error);
      // console.log('Message too long');
      return;
    }

    const selectedFriend = friendsData.find(
      (friend) => friend.user_id == selectedContact.dataset.contactId
    );
    const message = messageInput.value;
    const receiverId = selectedFriend.user_id;
    const receiverDisplayName = selectedFriend.display_name;
    const receiverAvatar = selectedFriend.avatar;
    const data = {
      type: 'chat',
      subtype: 'chat_message',
      sender_id: parseInt(userID, 10),
      receiver_id: receiverId,
      receiver_display_name: receiverDisplayName,
      receiver_avatar: receiverAvatar,
      message: message,
    };

    addSentChatMessage(message);
    sendMessagesBySocket(data, mainRoomSocket);
    // console.log('data:', data);
    messageInput.value = '';
  }

  sendButton?.addEventListener('click', sendChatMessage);

  messageInput?.addEventListener('keydown', function (event) {
    if (event.key === 'Enter') {
      event.preventDefault();
      sendChatMessage();
    }
  });
}


async function checkUnreadMessages() {
  const userID = g_user_id
  const data = {
    'type': 'chat',
    'subtype': 'check_unread_messages',
    'user_id': userID,
  };
  sendMessagesBySocket(data, mainRoomSocket);
}


function handleChatMessages(data) {
  if (data.subtype === 'init_listening') {
    init_listening();
    // console.log('chat listen init');
  }
  else if (data.subtype === 'chat_message') {
    const currentChatId = document.getElementById('currentChatId');
    if (currentChatId.value == data.sender_id) {
      addRecvChatMessage(data);
      // Update unread messages count
      markConversationRead(data.sender_id, data.receiver_id);
    }
    checkUnreadMessages();
  }
  else if (data.subtype === 'unread_messages') {
    // console.log('parseSocketMessage > data.subtype:', data.subtype);
    addUnreadMessages(data);
  } else if (data.subtype === 'load_conversation') {
    loadConversation(data);
    checkUnreadMessages();
  }

}


function loadConversation(data) {
  // console.log('loadConversation > data:', data);
  const conversation = document.getElementById('conversation');
  conversation.innerHTML = '';
  data.conversation.forEach(message => {
    if (message.sender_id == data.sender_id)
      addSentChatMessage(message.message);
    else
      addRecvChatMessage(message);
  });
}


function addSentChatMessage(message) {
  const chatMessages = document.getElementById('conversation');
  const messageElement = document.createElement('div');
  messageElement.classList.add('d-flex', 'flex-row', 'justify-content-end', 'mb-1');

  const messageContent = document.createElement('p');
  messageContent.classList.add('small', 'p-2', 'me-3', 'mb-0', 'rounded-3', 'bg-dark', 'text-white', 'text-break');
  messageContent.textContent = message;

  messageElement.appendChild(messageContent);
  chatMessages.appendChild(messageElement);
}


function addRecvChatMessage(data) {
  const chatMessages = document.getElementById('conversation');
  const messageElement = document.createElement('div');
  messageElement.classList.add('d-flex', 'flex-row', 'justify-content-start', 'mb-1');

  const messageContent = document.createElement('p');
  messageContent.classList.add('small', 'p-2', 'me-3', 'mb-0', 'rounded-3', 'bg-body-tertiary', 'text-break');
  messageContent.style.color = 'black';
  messageContent.textContent = data.message;

  messageElement.appendChild(messageContent);
  chatMessages.appendChild(messageElement);
  // console.log('addRecvChatMessage > data:', data);
}


function addUnreadMessages(data) {
  // console.log('addUnreadMessages > data:', data);
  const unreadChatsCount = document.getElementById('unreadChatscount');
  if (unreadChatsCount)
    unreadChatsCount.textContent = data.unread_messages_count;
}

function markConversationRead(sender_id, receiver_id) {
  // console.log('markConversationRead > sender_id:', sender_id, 'receiver_id:', receiver_id);
  const unreadMessagesData = {
    type: 'chat',
    subtype: 'mark_conversation_read',
    sender_id: sender_id,
    receiver_id: receiver_id,
  };
  sendMessagesBySocket(unreadMessagesData, mainRoomSocket);
}

async function getConversationBySocket(friend_id) {
  const userID = g_user_id;
  const messageData = {
    type: 'chat',
    subtype: 'get_conversation',
    sender_id: userID,
    receiver_id: friend_id,
  };
  sendMessagesBySocket(messageData, mainRoomSocket);
}

function toggleGameInvitePopup() {
  const gameInvitePopup = document.getElementById('gameInvitePopup');
  if (gameInvitePopup.style.display === 'block')
    gameInvitePopup.style.display = 'none';
  else
    gameInvitePopup.style.display = 'block';
}


async function getFriendsData() {
  const request = new Request('/getFriends/', {
    method: 'GET',
    headers: {
      'X-CSRFToken': getCookie('csrftoken'),
    },
    credentials: 'include',
  });

  try {
    const response = await fetch(request);
    const data = await response.json();
    // console.log('data:', data);
    return data.friends;
  } catch (error) {
    console.error('Error fetching friends:', error);
    return [];
  }
}


async function displayFriendsInChat(friendsData) {
  // Displays who called this function
  // console.log('displayFriendsInChat > friendsData: ', friendsData);
  const stackTrace = new Error().stack;
  // console.log('displayFriendsInChat > call stack:', stackTrace);

  const currentChatId = document.getElementById('currentChatId');
  const blockSwitchContainer = document.getElementById('blockSwitchContainer');
  const userID = g_user_id;

  // Reset header
  document.getElementById('contactContainer').style.display = 'none';
  currentChatId.value = '';
  blockSwitchContainer.style.display = 'none';
  document.getElementById('chat-modal-footer').style.display = 'none';

  // Reset conversation
  document.getElementById('conversation').innerHTML = '';

  const contactList = document.getElementById('contactList');
  // Clean the contact list
  contactList.innerHTML = '';
  if (friendsData.length === 0) {
    const noFriends = document.createElement('p');
    let lang = getCookie('django_language');
    let message = 'No friends yet';
    if (lang === 'fr')
      message = 'Aucun amis';
    else if (lang === 'es')
      message = 'Sin amigos aún';
    noFriends.textContent = message;
    noFriends.classList.add('no-friends-message');
    contactList.appendChild(noFriends);
    return;
  }

  friendsData.forEach((friend) => {
    checkIfImBlocked(friend.user_id).then((imBlocked) => {
      // Loop through every li of the contact list and return if the friend is already there: dataset.contactId = friend.user_id
      const contacts = contactList.getElementsByClassName('list-group-item');
      for (let c of contacts) {
        if (c.dataset.contactId == friend.user_id) {
          return;
        }
      }

      // Create a new contact item for the friend
      const contactItem = document.createElement('li');
      contactItem.classList.add(
        'list-group-item',
        'bg-transparent',
        'text-white',
        'custom-contact',
        'd-flex',
        'align-items-center',
        'p-3',
        'position-relative',
      );
      contactItem.dataset.contactId = friend.user_id;

      // Create avatar element
      const avatar = document.createElement('img');
      avatar.src = friend.avatar || "{% static 'images/default_avatar.png' %}";
      avatar.classList.add('rounded-circle', 'me-2');
      avatar.style.height = '2rem';
      avatar.style.width = '2rem';
      avatar.alt = 'avatar';

      // Display online status element if friend is not blocked (always create element)
      const onlineStatus = document.createElement('span');
      onlineStatus.classList.add('position-absolute', 'translate-middle', 'bg-success', 'online-status-chat');
      onlineStatus.dataset.online = friend.user_id;
      if (friend.online && !imBlocked)
        onlineStatus.style.display = 'block';
      else
        onlineStatus.style.display = 'none';

      // Create display name element
      const displayName = document.createElement('span');
      displayName.textContent = friend.display_name;

      // Add the avatar and display name to the contact item
      contactItem.appendChild(avatar);
      contactItem.appendChild(displayName);
      contactItem.appendChild(onlineStatus);

      // Add the contact item to the contact list
      contactList.appendChild(contactItem);

      if (imBlocked) {
        contactItem.classList.add('blocked-contact');
      } else {
        // Listen to the click event on the contact item
        contactItem.addEventListener('click', function (event) {
          // Remove the 'selected-contact' class from all contacts
          const contacts = contactList.getElementsByClassName('list-group-item');
          for (let c of contacts) {
            c.classList.remove('selected-contact');
          }
          // Add the 'selected-contact' class to the clicked contact
          contactItem.classList.add('selected-contact');

          document.getElementById('contactContainer').style.display = 'flex';
          document.getElementById('chat-modal-footer').style.display = 'flex';

          // Update the avatar and display name
          const contactAvatarAndName = document.getElementById('contactAvatarAndName');
          const contactAvatarLink = document.getElementById('contactAvatarLink');
          const contactDisplayNameLink = document.getElementById('contactDisplayNameLink');

          contactAvatarLink.href = '/userprofile/' + friend.user_id + '/';
          contactDisplayNameLink.href = '/userprofile/' + friend.user_id + '/';

          const newContactAvatarLink = contactAvatarLink.cloneNode(true);
          contactAvatarAndName.replaceChild(newContactAvatarLink, contactAvatarLink);
          const newContactDisplayNameLink = contactDisplayNameLink.cloneNode(true);
          contactAvatarAndName.replaceChild(newContactDisplayNameLink, contactDisplayNameLink);
          document.getElementById('contactDisplayName').textContent = friend.display_name;
          document.getElementById('contactAvatar').src = friend.avatar;

          newContactAvatarLink.addEventListener('click', function (event) {
            navigate(event, `/userprofile/${friend.user_id}`);
          });
          newContactDisplayNameLink.addEventListener('click', function (event) {
            navigate(event, `/userprofile/${friend.user_id}`);
          });
          setupChatNavigateEventListeners(calcGameSocket);

          currentChatId.value = friend.user_id;

          // update gameInvitePopup with friend.user_id
          const gameInvitePopup = document.getElementById('gameInvitePopup');
          const gameInviteForm = gameInvitePopup.querySelector('form');
          // console.log('gameInviteForm:', gameInviteForm);
          gameInviteForm.id = `chat-invite-play-${friend.user_id}`;
          gameInviteForm.action = `/invite_to_play/${friend.user_id}/`;
          const newGameInviteForm = gameInviteForm.cloneNode(true);
          gameInvitePopup.replaceChild(newGameInviteForm, gameInviteForm);
          listenForm(newGameInviteForm);

          // Add block switch
          blockSwitchContainer.style.display = 'block';
          const blockSwitch = blockSwitchContainer.querySelector('input');
          const blockSwitchDiv = blockSwitchContainer.querySelector('#blockSwitchDiv');
          blockSwitch.setAttribute('data-user-id', friend.user_id);
          blockSwitch.setAttribute('id', `blockSwitch-${friend.user_id}`);
          // Cloning and replacing the blockSwitch before adding event listener to avoid duplicates
          const newBlockSwitch = blockSwitch.cloneNode(true);
          blockSwitchDiv.replaceChild(newBlockSwitch, blockSwitch);
          checkIfBlocked(friend.user_id).then((isBlocked) => {
            // console.log('chat checkIfBlocked > isBlocked:', isBlocked);
            newBlockSwitch.checked = isBlocked;
            if (isBlocked) {
              document.getElementById('contactGameInviteContainer').style.display = 'none';
              document.getElementById('chat-modal-footer').style.display = 'none';
            }
            else {
              document.getElementById('contactGameInviteContainer').style.display = 'flex';
              document.getElementById('chat-modal-footer').style.display = 'flex';
              document.getElementById('messageInput').value = '';
            }
            // messageInput.placeholder = isBlocked
            //   ? 'You cannot send messages to blocked users'
            //   : 'Type a message to send';
          });
          newBlockSwitch.addEventListener('change', function () {
            // console.log('blockSwitch changed');
            sendBlockInfoToSocket(userID, friend.user_id, newBlockSwitch.checked);
            blockFriend(friend.user_id);
            // Send info to the websocket
          });

          // Get all the messages between the user and the selected friend
          getConversationBySocket(friend.user_id);
        });
      }

    });
  });
}

async function updateFriendsState() {

  let friendsData = await getFriendsData();
  displayFriendsInChat(friendsData);

  if (window.location.pathname.includes('my_friends')) {
    loadContent(window.location.pathname);
  }

}