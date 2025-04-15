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
  private fpsText!: Phaser.GameObjects.Text;
  private pingText!: Phaser.GameObjects.Text;
  private pingInterval = 0;
  private lastPingSentTime = 0;
  
  // Player input setup
  private cursors!: Phaser.Types.Input.Keyboard.CursorKeys;
  
  // World variables
  private background!: Phaser.GameObjects.Graphics;
  private player!: Blob;
  private otherPlayers: { [id: string]: Blob } = {};
  private playerID!: string;
  private food: { [id: string]: Phaser.GameObjects.Graphics } = {};
  private score: number;

  // For server reconciliation and client prediction
  private input_send: number = 0;
  private clientBlob!: Blob;
  private unprocessed_inputs: PlayerInput[] = [];

  private useClientPrediction = true;
  private useLerp = true;



  constructor() {
    super("Game");
  }

  create(data: any) {

    // Lag and Packet Loss UI
    if (!document.getElementById("network-controls")) {
      const ui = document.createElement("div");
      ui.id = "network-controls";
      ui.style.position = "fixed";
      ui.style.top = "10px";
      ui.style.right = "10px";
      ui.style.padding = "10px";
      ui.style.background = "rgba(0, 0, 0, 0.7)";
      ui.style.color = "white";
      ui.style.borderRadius = "8px";
      ui.style.width = "220px";
      ui.style.zIndex = "1000";
      ui.style.fontFamily = "sans-serif";
      ui.innerHTML = `
        <label>Simulate Lag (ms): <span id="lagValue">30</span></label>
        <input type="range" id="lagSlider" min="0" max="500" value="30" style="width: 100%">
        <br/><br/>
        <label>Packet Loss (%): <span id="lossValue">0</span></label>
        <input type="range" id="lossSlider" min="0" max="100" value="0" style="width: 100%">
        <br/><br/>
        <label>
          <input type="checkbox" id="toggleCSP" checked />
          Enable Client-Side Prediction
        </label>
        <br/>
        <label>
          <input type="checkbox" id="toggleLERP" checked />
          Enable LERP for Other Players
        </label>
      `;
      document.body.appendChild(ui);
    
      // Live updating display
      document.getElementById("lagSlider")?.addEventListener("input", (e: any) => {
        document.getElementById("lagValue")!.innerText = e.target.value;
      });
      document.getElementById("lossSlider")?.addEventListener("input", (e: any) => {
        document.getElementById("lossValue")!.innerText = e.target.value;
      });
    }

    (document.getElementById("toggleCSP") as HTMLInputElement)?.addEventListener("change", (e: any) => {
      this.useClientPrediction = e.target.checked;
    
      if (this.useClientPrediction) {
        this.cameras.main.startFollow(this.clientBlob, true, 0.1, 0.1);
        this.player.setAlpha(0.5);
        this.clientBlob.setVisible(true);
      } else {
        this.cameras.main.startFollow(this.player, true, 0.1, 0.1);
        this.player.setAlpha(1);
        this.clientBlob.setVisible(false);
      }
    });
    
    (document.getElementById("toggleLERP") as HTMLInputElement)?.addEventListener("change", (e: any) => {
      this.useLerp = e.target.checked;
    });

    this.playerID = data?.playerID;

    this.socket = new WebSocket(`ws://localhost:8000/ws/game/${this.playerID}/`);

    window.addEventListener("beforeunload", () => {
      this.socket.close();
    });

    this.socket.onopen = () => {
      console.log("Connected to WebSocket server");
    };

    // Handles incoming messages from server
    this.socket.onmessage = (event) => {

      const lagSlider = document.getElementById("lagSlider") as HTMLInputElement;
      const lossSlider = document.getElementById("lossSlider") as HTMLInputElement;
      const lag = Number(lagSlider?.value || 0);
      const loss = Number(lossSlider?.value || 0);
      
      // simulate packet loss
      if (Math.random() * 100 < loss) {
        return; 
      }

      const data = JSON.parse(event.data);
      
      //simulate lag
      setTimeout(() => {
        this.handleServerMessage(data);
      }, lag);
    
    }
    // Create background with grid
    this.background = this.add.graphics();
    this.drawGrid(50, 2000, 2000);

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
    if (this.useClientPrediction) {
      this.clientBlob.move(dx, dy, (delta / 1000));
    }

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

    // Smooth updates for other players
    if (this.useLerp) {
      for (const id in this.otherPlayers) {
        this.otherPlayers[id].updateInterpolatedPosition();
      }
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
      if (!this.player){
        this.player = new Blob(this, data.players[this.playerID].x,data.players[this.playerID].y, data.players[this.playerID].size, parseInt("#CC8899"), data.players[this.playerID].name);
        this.player.setAlpha(0.5);

        // player seen by the client
        this.clientBlob = new Blob(this, data.players[this.playerID].x,data.players[this.playerID].y, data.players[this.playerID].size, parseInt(data.players[this.playerID].color), data.players[this.playerID].name);
        this.cameras.main.startFollow(this.clientBlob, true, 0.1, 0.1);
        this.cameras.main.setZoom(1);

        this.score = data.players[this.playerID].score;
      }
      

      for (const id in data.players) {
        if (String(id) !== String(this.playerID) && !this.otherPlayers[id]) {
            const { x, y, size, color, name } = data.players[id];
            this.otherPlayers[id] = new Blob(this, x, y, size, color, name);
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
      if ((String(data.id) !== String(this.playerID)) && !this.otherPlayers[data.id]) {
        this.otherPlayers[data.id] = new Blob(this, data.x, data.y, data.size, data.color, data.name);
      }
    }

    if (data.type === "player_left"){
      console.log("Received Data:", data);
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
        this.player.setPos(data.x, data.y);

        //Reconciles client
        const serverLastInput = data.last_input_processed;
        this.unprocessed_inputs = this.unprocessed_inputs.filter(
          input => input.seq_num > serverLastInput
        );
        this.clientBlob.x = data.x;
        this.clientBlob.y = data.y;
        this.clientBlob.setPos(data.x, data.y);

        for (const input of this.unprocessed_inputs){
          this.clientBlob.move(
            input.direction.dx,
            input.direction.dy,
            input.delta/1000
          )
        }
      }
      else {
        if (this.useLerp) {
          this.otherPlayers[data.id].setTargetPosition(data.x, data.y);
        } else {
          this.otherPlayers[data.id].x = data.x;
          this.otherPlayers[data.id].y = data.y;
          this.otherPlayers[data.id].setPos(data.x, data.y);
        }
      }
    }

    if (data.type === "food_eaten") {
      if (this.food[data.id]) {
        this.food[data.id].destroy();
        delete this.food[data.id];
      }

      if (String(data.player_id) === String(this.playerID)) {
        this.score = data.score;
        this.player.setSize(data["size"]);
        this.clientBlob.setSize(data["size"]);
      }
      else{
        this.otherPlayers[data.player_id].setSize(data["size"]);
      }
    }

    if (data.type === "spawn_food"){
      const foodObj = this.add.graphics();
      foodObj.fillStyle(0xff0000, 1); // Red color
      foodObj.fillCircle(0, 0, 5);
      foodObj.setPosition(data.food.x, data.food.y);
      this.food[data.food.id] = foodObj;
    }

    if (data.type === "player_eaten") {
      if (String(data.id) !== String(this.playerID)) {
        this.otherPlayers[data.id].destroy();
        delete this.otherPlayers[data.id];
      }
      else{
        this.player.destroy();
        this.clientBlob.destroy();
        this.socket.close();
      }

      if (String(data.id_eater) === String(this.playerID)) {
        this.player.setSize(data.size);
        this.clientBlob.setSize(data.size);
      }
      else{
        this.otherPlayers[data.id_eater].setSize(data.size);
      }

    }

    if (data.type === "pong" && typeof data.time === "number") {
      const now = Date.now();
      const ping = now - data.time;
      this.pingText.setText(`Ping: ${ping} ms`);
    }
  }


}

