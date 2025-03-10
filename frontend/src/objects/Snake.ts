import Phaser from "phaser";

export default class Snake {
  private scene: Phaser.Scene;
  private snake: Phaser.GameObjects.Graphics[] = [];
  private segmentSpacing = 10;
  private speed = 100; 
  private turnSpeed = 5;
  private currentAngle: number = 0;

  constructor(scene: Phaser.Scene, length: number) {
    this.scene = scene;

    for (let i = 0; i < length; i++) {
      const segment = this.scene.add.graphics();
      segment.fillStyle(0xff0000, 1);
      segment.fillCircle(0, 0, 10);
      this.snake.push(segment);
    }

    for (let i = 0; i < this.snake.length; i++) {
      this.snake[i].x = this.scene.cameras.main.centerX - i * this.segmentSpacing;
      this.snake[i].y = this.scene.cameras.main.centerY;
    }

    scene.cameras.main.startFollow(this.snake[0], true, 0.1, 0.1);
  }

  update(delta: number, cursors: Phaser.Types.Input.Keyboard.CursorKeys) {
    if (this.snake.length === 0) return;

    const deltaFactor = delta / 1000;
    const head = this.snake[0];

    if (cursors.left.isDown) {
      this.currentAngle -= this.turnSpeed * deltaFactor;
    } else if (cursors.right.isDown) {
      this.currentAngle += this.turnSpeed * deltaFactor;
    }

    // Move the head forward in the current direction
    head.x += Math.cos(this.currentAngle) * this.speed * deltaFactor;
    head.y += Math.sin(this.currentAngle) * this.speed * deltaFactor;

    // Move the rest of the body segments
    for (let i = this.snake.length - 1; i > 0; i--) {
      const prevSegment = this.snake[i - 1];
      const currSegment = this.snake[i];

      const distance = Phaser.Math.Distance.Between(
        currSegment.x,
        currSegment.y,
        prevSegment.x,
        prevSegment.y
      );

      if (distance > this.segmentSpacing) {
        const angle = Phaser.Math.Angle.Between(
          currSegment.x,
          currSegment.y,
          prevSegment.x,
          prevSegment.y
        );
        currSegment.x = prevSegment.x - Math.cos(angle) * this.segmentSpacing;
        currSegment.y = prevSegment.y - Math.sin(angle) * this.segmentSpacing;
      }
    }
  }
}
