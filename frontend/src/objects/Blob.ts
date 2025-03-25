import Phaser from "phaser";

export class Blob {
    scene: Phaser.Scene;
    graphics: Phaser.GameObjects.Graphics;
    baseSpeed: number;
    radius: number;
    x: number;
    y: number;

    constructor(scene: Phaser.Scene, x: number, y: number, radius:number = 20,color: number = 0x00ff00) {
        this.scene = scene;
        this.baseSpeed = 150;
        this.radius = radius;
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

        const intended_x = this.x + (dx * this.baseSpeed * delta);
        const intended_y = this.y + (dy * this.baseSpeed * delta);
        this.x = Math.max(0, Math.min(intended_x, 1000));
        this.y = Math.max(0, Math.min(intended_y, 1000));

        this.graphics.setPosition(this.x, this.y);
    }

    getPosition() {
        return { x: this.x, y: this.y };
    }

    destroy() {
        this.graphics.destroy(); 
    }

}
