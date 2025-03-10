import Phaser from "phaser";

export class Blob {
    scene: Phaser.Scene;
    graphics: Phaser.GameObjects.Graphics;
    baseSpeed: number;
    radius: number;
    x: number;
    y: number;

    constructor(scene: Phaser.Scene, x: number, y: number, color: number = 0x00ff00) {
        this.scene = scene;
        this.baseSpeed = 150;
        this.radius = 20;
        this.x = x;
        this.y = y;


        this.graphics = this.scene.add.graphics();
        this.drawBlob(color);
        this.graphics.setPosition(this.x, this.y);
    }

    private drawBlob(color: number) {
        this.graphics.clear();
        this.graphics.fillStyle(color, 1);
        this.graphics.fillCircle(0, 0, this.radius);
    }

    move(dx: number, dy: number, delta: number) {
        const speedFactor = delta / 1000; 
        this.x += dx * this.baseSpeed * speedFactor;
        this.y += dy * this.baseSpeed * speedFactor;

        this.graphics.setPosition(this.x, this.y);
    }

    getPosition() {
        return { x: this.x, y: this.y };
    }
}
