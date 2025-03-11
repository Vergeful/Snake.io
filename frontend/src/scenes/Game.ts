import { Scene } from "phaser";
import { Blob } from "../objects/Blob";

export class Game extends Scene {
  private socket!: WebSocket;
  private background!: Phaser.GameObjects.Graphics;
  private cursors!: Phaser.Types.Input.Keyboard.CursorKeys;
  private player!: Blob;
  private fpsText!: Phaser.GameObjects.Text;
  private otherPlayers: { [id: string]: Blob } = {};
  private playerID!: string;
  private food: { [id: string]: Phaser.GameObjects.Graphics } = {};
  private score: number;


  constructor() {
    super("Game");
  }

  create(data: any) {
    // Enable physics world with boundaries

    const playerNmae = data?.playerName;
    const playerColor = data?.playerColor;
    this.playerID = data?.playerID;

    this.socket = new WebSocket(`ws://localhost:8000/ws/game/${this.playerID}/`);

    this.socket.onopen = () => {
      console.log("Connected to WebSocket server");
    };

    this.socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log("Received Data:", data);
      if (data.type === "all_players"){
        this.player = new Blob(this, data.players[this.playerID].x,data.players[this.playerID].y, data.players[this.playerID].size, parseInt(data.players[this.playerID].color))
        this.cameras.main.startFollow(this.player, true, 0.1, 0.1);
        this.cameras.main.setZoom(1);

        this.score = data.players[this.playerID].score;

        for (const id in data.players) {
          if (String(id) !== String(this.playerID)) {
              const { x, y } = data.players[id];
              this.otherPlayers[id] = new Blob(this, x, y);
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


      if (data.type === "update") {
        if (data.id === this.playerID) {
          //Server updates local player position
          this.player.x = data.x;
          this.player.y = data.y;
          this.player.graphics.setPosition(data.x, data.y);
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

    // Character movement
    this.cursors = this.input.keyboard!.createCursorKeys();

  }

  update(time: number, delta: number) {
    const fps = Math.floor(this.game.loop.actualFps);
    this.fpsText.setText(`Score: ${this.score}`);

    if (!this.cursors || !this.player) return;

    let dx = 0, dy = 0;
    if (this.cursors.left?.isDown) dx = -1;
    if (this.cursors.right?.isDown) dx = 1;
    if (this.cursors.up?.isDown) dy = -1;
    if (this.cursors.down?.isDown) dy = 1;

    if (this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(
        JSON.stringify({
          type: "move",
          id: this.playerID,
          x: this.player.x + dx  * (delta/1000) * this.player.baseSpeed,
          y: this.player.y + dy * (delta/1000) * this.player.baseSpeed,
        })
      );
    }
  
  }

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
}
