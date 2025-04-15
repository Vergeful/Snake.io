import Phaser from "phaser";

export class Blob {
  scene: Phaser.Scene;
  container: Phaser.GameObjects.Container;
  graphics: Phaser.GameObjects.Graphics;
  nameText: Phaser.GameObjects.Text;
  baseSpeed: number;
  radius: number;
  x: number;
  y: number;
  color: number;

  private targetX: number;
  private targetY: number;

  private fontScale: number = 0.5;

  constructor(
    scene: Phaser.Scene,
    x: number,
    y: number,
    radius: number = 20,
    color: number = 0x00ff00,
    name: string = "Player"
  ) {
    this.scene = scene;
    this.baseSpeed = 150;
    this.radius = radius;
    this.x = x;
    this.y = y;
    this.color = color;

    this.targetX = x;
    this.targetY = y;

    // Create graphics (the blob circle)
    this.graphics = this.scene.add.graphics();
    this.drawBlob();

    // Create text for the player's name
    this.nameText = this.scene.add.text(0, 0, name, {
      fontSize: `${radius * this.fontScale}px`,
      color: "#ffffff",
      fontFamily: "Arial",
    }).setOrigin(0.5);

    // Create container and add graphics + text
    this.container = this.scene.add.container(x, y, [this.graphics, this.nameText]);
  }

  private drawBlob() {
    const darkerColor = Phaser.Display.Color.ValueToColor(this.color).darken(25).color;

    this.graphics.clear();
    this.graphics.lineStyle(4, darkerColor, 1);
    this.graphics.fillStyle(this.color, 1);
    this.graphics.strokeCircle(0, 0, this.radius);
    this.graphics.fillCircle(0, 0, this.radius);
  }

  move(dx: number, dy: number, delta: number) {
    const intended_x = this.x + dx * this.baseSpeed * delta;
    const intended_y = this.y + dy * this.baseSpeed * delta;

    this.x = Phaser.Math.Clamp(intended_x, 0, 2000);
    this.y = Phaser.Math.Clamp(intended_y, 0, 2000);

    this.container.setPosition(this.x, this.y);
  }

  setTargetPosition(x: number, y: number) {
    this.targetX = x;
    this.targetY = y;
  }

  updateInterpolatedPosition() {
    const alpha = 0.1;
    this.x = Phaser.Math.Linear(this.x, this.targetX, alpha);
    this.y = Phaser.Math.Linear(this.y, this.targetY, alpha);
    this.container.setPosition(this.x, this.y);
  }

  getPosition() {
    return { x: this.x, y: this.y };
  }

  destroy() {
    this.container.destroy(); 
  }

  setSize(newSize: number) {
    this.radius = newSize;
    this.drawBlob();
    this.nameText.setFontSize(`${newSize * this.fontScale}px`);
  }

  setAlpha(value: number) {
    this.container.setAlpha(value);
  }

  setVisible(value: boolean) {
    this.container.setVisible(value);
  }

  setPos(x:number, y:number){
    this.container.setPosition(x,y);
  }
}
