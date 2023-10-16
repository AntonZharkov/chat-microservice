const socket = new WebSocket('ws://localhost:8001/ws/chat/')

function receiveMessage (e) {
  const data = JSON.parse(e.data)
  const command = data.type
  switch (command) {
    case 'new_message_event':
      newMessageEvent(data.data)
      break
  }
}

const onClose = (e) => {
  console.log(`onClose: ${e}`)
}

socket.onopen = e => {}
socket.onclose = onClose
socket.onmessage = receiveMessage

const writeMessage = JSON.stringify({
  'command': 'write_message',
  data: {
    'author': 1,
  }
})

$('#chat-message-submit').on('click', newMessageHandler)

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

function newMessageEvent(data) {
  const messageHTML = generateNewMessageHTML(data)
  document.querySelector('.chat-messages').insertAdjacentHTML('beforeend', messageHTML)
}
