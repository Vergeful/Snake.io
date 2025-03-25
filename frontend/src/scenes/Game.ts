import { Scene } from "phaser";
import { Blob } from "../objects/Blob";

interface PlayerInput{
  seq_num: number;
  direction: {
    dx: number;
    dy: number;
  }
  delta: number;
}

export class Game extends Scene {
  private socket!: WebSocket;
  private background!: Phaser.GameObjects.Graphics;
  private cursors!: Phaser.Types.Input.Keyboard.CursorKeys;
  private player!: Blob;
  private fpsText!: Phaser.GameObjects.Text;
  private pingText!: Phaser.GameObjects.Text;
  private pingInterval = 0;
  private lastPingSentTime = 0;
  private otherPlayers: { [id: string]: Blob } = {};
  private playerID!: string;
  private food: { [id: string]: Phaser.GameObjects.Graphics } = {};
  private score: number;
  private input_send: number = 0;
  private clientBlob!: Blob;
  private unprocessed_inputs: PlayerInput[] = [];



  constructor() {
    super("Game");
  }

  create(data: any) {

    this.playerID = data?.playerID;

    this.socket = new WebSocket(`ws://localhost:8000/ws/game/${this.playerID}/`);

    this.socket.onopen = () => {
      console.log("Connected to WebSocket server");
    };

    // Handles incoming messages from server
    this.socket.onmessage = (event) => {
      
      // simulate packet loss
      // if (Math.random() < 0.4) {
      //   return; 
      // }

      const data = JSON.parse(event.data);
      
      //simulate lag
      setTimeout(() => {
        this.handleServerMessage(data);
      }, 0);
    
    }
    // Create background with grid
    this.background = this.add.graphics();
    this.drawGrid(50, 1000, 1000);

    // FPS display
    this.fpsText = this.add.text(10, 10, "FPS: 0", {
      fontSize: "18px",
      color: "#ffffff",
      backgroundColor: "#000000",
    }).setScrollFactor(0);


    // Ping display
    this.pingText = this.add.text(10, 30, "Ping: -- ms", {
      fontSize: "18px",
      color: "#ffffff",
      backgroundColor: "#000000",
    }).setScrollFactor(0);


    // Character movement
    this.cursors = this.input.keyboard!.createCursorKeys();

  }

  update(time: number, delta: number) {

    // show game stats (debugging)
    const fps = Math.floor(this.game.loop.actualFps);
    this.fpsText.setText(`FPS: ${fps}`);

    if (!this.cursors || !this.player) return;

    let dx = 0, dy = 0;
    if (this.cursors.left?.isDown) dx += -1;
    if (this.cursors.right?.isDown) dx += 1;
    if (this.cursors.up?.isDown) dy += -1;
    if (this.cursors.down?.isDown) dy += 1;

    // Client side prediction for smooth gameplay
    this.clientBlob.move(dx,dy,(delta/1000));

    // Updates unprocessed inputs list
    if (this.socket.readyState === WebSocket.OPEN && (dx || dy)) {
      this.input_send++;
      const player_input: PlayerInput = {
        seq_num: this.input_send,
        direction: {
          dx: dx,
          dy: dy,
        },
        delta: delta,
      }
      this.unprocessed_inputs.push(player_input);
      console.log(this.unprocessed_inputs);

      // sends move message to server
      this.socket.send(
        JSON.stringify({
          type: "move",
          id: this.playerID,
          direction: {
            dx: dx,
            dy: dy,
          },
          input_number: this.input_send
        })
      );
    }

    this.pingInterval += delta;
    if (this.pingInterval >= 1000) {
      this.lastPingSentTime = Date.now();

      this.socket.send(JSON.stringify({
        type: "ping",
        time: this.lastPingSentTime,
      }));

      this.pingInterval = 0;
    }
  
  }

  // utitlity function for drawing grid to world
  private drawGrid(gridSize: number, worldWidth: number, worldHeight: number) {
    this.background.lineStyle(1, 0xcccccc, 1);

    for (let x = 0; x <= worldWidth; x += gridSize) {
      this.background.moveTo(x, 0);
      this.background.lineTo(x, worldHeight);
    }

    for (let y = 0; y <= worldHeight; y += gridSize) {
      this.background.moveTo(0, y);
      this.background.lineTo(worldWidth, y);
    }

    this.background.strokePath();
  }

  handleServerMessage(data: any){

    // for debugging
    if(data.type !== "update"){
      console.log("Received Data:", data);
    }


    if (data.type === "all_players"){
      // player seen by the server
      this.player = new Blob(this, data.players[this.playerID].x,data.players[this.playerID].y, data.players[this.playerID].size, parseInt("#CC8899"));
      this.player.graphics.setAlpha(0.5);

      // player seen by the client
      this.clientBlob = new Blob(this, data.players[this.playerID].x,data.players[this.playerID].y, data.players[this.playerID].size, parseInt(data.players[this.playerID].color));
      this.cameras.main.startFollow(this.clientBlob, true, 0.1, 0.1);
      this.cameras.main.setZoom(1);

      this.score = data.players[this.playerID].score;

      for (const id in data.players) {
        if (String(id) !== String(this.playerID)) {
            const { x, y, size, color } = data.players[id];
            this.otherPlayers[id] = new Blob(this, x, y, size, color);
        }
      }

      for (const food of data.food) {
        const foodObj = this.add.graphics();
        foodObj.fillStyle(0xff0000, 1); // Red color
        foodObj.fillCircle(0, 0, 5);
        foodObj.setPosition(food.x, food.y);
        this.food[food.id] = foodObj;
      }
    }

    if (data.type === "player_joined"){
      if (String(data.id) !== String(this.playerID)) {
        this.otherPlayers[data.id] = new Blob(this, data.x, data.y, data.size, data.color);
      }
    }

    if (data.type === "player_left"){
      if (String(data.id) !== String(this.playerID)) {
        this.otherPlayers[data.id].destroy();
        delete this.otherPlayers[data.id];
      }
    }


    if (data.type === "update") {
      if (String(data.id) === String(this.playerID)) {
        //Server updates local player position
        this.player.x = data.x;
        this.player.y = data.y;
        this.player.graphics.setPosition(data.x, data.y);

        //Reconciles client
        const serverLastInput = data.last_input_processed;
        this.unprocessed_inputs = this.unprocessed_inputs.filter(
          input => input.seq_num > serverLastInput
        );
        this.clientBlob.x = data.x;
        this.clientBlob.y = data.y;
        this.clientBlob.graphics.setPosition(data.x, data.y);

        for (const input of this.unprocessed_inputs){
          this.clientBlob.move(
            input.direction.dx,
            input.direction.dy,
            input.delta/1000
          )
        }
      }
      else {
        this.otherPlayers[data.id]
        this.otherPlayers[data.id].x = data.x;
        this.otherPlayers[data.id].y = data.y;
        this.otherPlayers[data.id].graphics.setPosition(data.x, data.y);
      }
    }

    if (data.type === "food_eaten") {
      if (this.food[data.id]) {
        this.food[data.id].destroy();
        delete this.food[data.id];
      }

      if (data.player_id === this.playerID) {
        this.score = data.score;
      }
    }

    if (data.type === "pong" && typeof data.time === "number") {
      const now = Date.now();
      const ping = now - data.time;
      this.pingText.setText(`Ping: ${ping} ms`);
    }
  }


}

