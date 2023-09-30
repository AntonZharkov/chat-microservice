const socket = new WebSocket('ws://localhost:8001/ws/chat/')

function receiveMessage (e) {
  console.log(`Receive message: ${e}`)
}

const onClose = (e) => {
  console.log(`onClose: ${e}`)
}

socket.onopen = e => {}
socket.onclose = onClose
socket.onmessage = receiveMessage

const newMessage = JSON.stringify({
  'command': 'new_message',
  'data': {
    'author': 1,
    'message': 'Hello',
    'chat_id': 'd66757cf82f64e48a79ea457d058e586'
  }
})

const writeMessage = JSON.stringify({
  'command': 'write_message',
  data: {
    'author': 1,
  }
})
