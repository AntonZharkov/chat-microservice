const socket = new WebSocket('ws://localhost:8001/ws/chat/')

function receiveMessage (e) {
  const data = JSON.parse(e.data)
  const command = data.type
  
  switch (command) {
    case 'new_message_event':
      newMessageEvent(data.data)
      break
    case 'write_message_event':
      writeMessageEvent(data.data)
      break
    case 'new_chat_event':
      newChatEvent(data.data)
      break
    case 'user_online_event':
      userOnlineEvent(data.data)
      break
  }
}

const onClose = (e) => {
  console.log(`onClose: ${e}`)
}

socket.onopen = e => {}
socket.onclose = onClose
socket.onmessage = receiveMessage

const debouncedHandlerWriteMessage = debounce(writeMessage, 100);
const debouncedHandlerStopWriteMessage = debounce(stopWriteMessage, 1500);

$('#chat-message-submit').on('click', newMessageHandler)
$('#chat-message-input').on('keydown', debouncedHandlerWriteMessage)
$('#chat-message-input').on('keyup', debouncedHandlerStopWriteMessage)

function newMessageHandler(event) {
  const message = $('#chat-message-input')[0].value
  const activeChat = $('.active')[0]
  const chat_id = activeChat ? activeChat.id : ''

  if (chat_id && message) {
    $('#chat-message-input')[0].value = ''
    data = JSON.stringify({
      'command': 'new_message',
      'data': {
        'chat_id': chat_id,
        'body': message
      }
    })

    socket.send(data)
  }
}

function writeMessage(event) {
  user = JSON.parse(localStorage.getItem('user'))
  const activeChat = $('.active')[0]
  const chat_id = activeChat ? activeChat.id : ''
  // проверяем что мы перешли в чат, а не пишем без выбранного чата
  if (chat_id) {
    data = JSON.stringify({
      'command': 'write_message',
      'data': {
        'author': user.id,
        'full_name': user.full_name,
        'chat_id': chat_id,
        'typing': true,
      }
    })

    socket.send(data)
  }
}

function stopWriteMessage(event) {
  user = JSON.parse(localStorage.getItem('user'))
  const activeChat = $('.active')[0]
  const chat_id = activeChat ? activeChat.id : ''
  if (chat_id) {
    data = JSON.stringify({
      'command': 'write_message',
      'data': {
        'author': user.id,
        'full_name': user.full_name,
        'chat_id': chat_id,
        'typing': false,
      }
    })

    socket.send(data)
  }
}

function generateNewMessageHTML(data) {
  data.created = formatDate(data.created)
  user = JSON.parse(localStorage.getItem('user'))
  let messageClass = 'chat-message-left'

  if (data.user.id === user.id) {
    messageClass = 'chat-message-right'
  }

  return `
  <div class="${messageClass} pb-4">
    <div>
      <img src="${data.user.avatar}" class="rounded-circle mr-1" alt="${data.user.full_name}" width="40" height="40">
      <div class="text-muted small text-nowrap mt-2">${data.created} </div>
    </div>
    <div class="flex-shrink-1 bg-light rounded py-2 px-3 mr-3">
      <div class="font-weight-bold mb-1">${data.user.full_name}</div>
      ${data.body}
    </div>
  </div>
  `
}

function generateChat(data) {
  return `
  <li id=${data.chat_id} class="clearfix chats">
    <img src="${data.user.avatar}" alt="avatar">
    <div class="about">
        <div class="name">${data.user.full_name}</div>
        <div class="status"> <i class="fa fa-circle offline"></i> left 7 mins ago </div>
    </div>
  </li>
`
}

function newMessageEvent(data) {
  // Находимся ли в чате в котором написали новое сообщение
  if ($(`#${data.chat_id}`).hasClass('active')) {
    // если да то добавляем новое сообщение
    const messageHTML = generateNewMessageHTML(data)
    document.querySelector('.chat-messages').insertAdjacentHTML('beforeend', messageHTML)
  } else {
    const badgeExists = $(`#${data.chat_id}`).find('span.badge').length > 0;

    // если нет то добавляем к текущему количеству непрочитанных сообщений еще одно
    if (badgeExists) {
      $(`#${data.chat_id} span.badge`).text(function(index, text) {
        const currentValue = parseInt(text);
        const newValue = currentValue + 1;
        return newValue;
      });
    } else {
      // если первое непрочитанное сообщение то добавляем спан с одним сообщением
      $(`#${data.chat_id}`).append(`<span class="badge badge-pill badge-primary" style="margin: 10px 5px;">1</span>`);
    }
    const chat = $(`#${data.chat_id}`)
    // переносим чат наверх
    chat.remove()
    chat.prependTo('.chat-list')
    chat.on('click', getMessages)
  }
}

function writeMessageEvent(data) {
  user = JSON.parse(localStorage.getItem('user'))

  // Проверяем, что текущий пользователь не является пользователем, который пишет
  // и проверяем на то что мы находимся в том чате, где пишет пользователь
  if (user.id !== data.author && $(`#${data.chat_id}`).hasClass('active')) {
    const typingHTML = `<small class="typing">${data.full_name} typing<span class="dots"> </span></small>`
    const chatAbout = $('.chat-about')
    const typingClass = chatAbout.find('.typing')

    // Проверяем на то что пользователь пишет и подпись 'User typing' еще не добавлена
    if (data.typing && typingClass.length === 0) {
      chatAbout.append(typingHTML)
    } else if (data.typing === false) {
      typingClass.remove()
    }
  }
}

function newChatEvent(data) {
  chat = $(`#${data.id}`)
  const chatHTML = generateChat(data)
  document.querySelector('.chat-list').insertAdjacentHTML('afterbegin', chatHTML);
}

// Добавление статуса онлайн/оффлайн
function userOnlineEvent(data) {
  const user = JSON.parse(localStorage.getItem('user'));
  const statusElement = $(`#${data.chat_id} .status`);
  const statusNameTitle = $('.chat-about small');

  // Проверяем, что текущий пользователь не является пользователем, чей статус обновляется
  if (user.full_name !== data.user_name) {
    const onlineIcon = '<i class="fa fa-circle online"></i>';
    const offlineIcon = '<i class="fa fa-circle offline"></i>';
    const onlineStatus = `${onlineIcon} Online`;
    const offlineStatus = `${offlineIcon} Offline`;

    // Обновляем статус элемента .status
    if (data.online) {

      statusElement.html(onlineStatus);
      if (statusNameTitle) {
        statusNameTitle.html(onlineStatus);
      }
    } else {
      statusElement.html(offlineStatus);
      if (statusNameTitle) {
        statusNameTitle.html(offlineStatus);
      }
    }
  }
}

// обертка для вызова функции спустя заданное время
function debounce(func, delay) {
  let timeout;
  return function() {
    const context = this;
    const args = arguments;
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(context, args), delay);
  };
}
