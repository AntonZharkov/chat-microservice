const socket = new WebSocket('ws://localhost:8000/ws/chat/12/')

const receiveMessage = (e) => {
  console.log(`Receive message: ${e}`)
}

const onClose = (e) => {
  console.log(`onClose: ${e}`)
}

socket.onopen = e => {}
socket.onclose = onClose
socket.onmessage = receiveMessage

