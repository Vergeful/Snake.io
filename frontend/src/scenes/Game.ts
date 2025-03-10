import { Scene } from "phaser";
import { Blob } from "../objects/Blob";

export class Game extends Scene {
  private background!: Phaser.GameObjects.Graphics;
  private cursors!: Phaser.Types.Input.Keyboard.CursorKeys;
  private player!: Blob;
  private fpsText!: Phaser.GameObjects.Text;

  constructor() {
    super("Game");
  }

  create() {
    // Enable physics world with boundaries
    this.physics.world.setBounds(0, 0, 1000, 1000); 

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

    // Create player
    this.player = new Blob(this, 0, 0);

    // Make camera follow the container (not just the graphics)
    this.cameras.main.startFollow(this.player, true, 0.05, 0.05);
    this.cameras.main.setZoom(1);
  }

  update(time: number, delta: number) {
    const fps = Math.floor(this.game.loop.actualFps);
    this.fpsText.setText(`FPS: ${fps}`);

    if (!this.cursors || !this.player) return;

    let dx = 0, dy = 0;
    if (this.cursors.left?.isDown) dx = -1;
    if (this.cursors.right?.isDown) dx = 1;
    if (this.cursors.up?.isDown) dy = -1;
    if (this.cursors.down?.isDown) dy = 1;

    this.player.move(dx, dy, delta);
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
