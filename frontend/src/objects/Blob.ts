import Phaser from "phaser";

export class Blob {
    scene: Phaser.Scene;
    container: Phaser.GameObjects.Container;
    graphics: Phaser.GameObjects.Graphics;
    body: Phaser.Physics.Arcade.Body;
    baseSpeed: number;
    radius: number;

    constructor(scene: Phaser.Scene, x: number, y: number, color: number = 0x00ff00) {
        this.scene = scene;
        this.baseSpeed = 200; // Movement speed
        this.radius = 20;

        // Create a graphics object for the blob
        this.graphics = this.scene.add.graphics();
        this.drawBlob(0, 0, color);

        const physicsBody = this.scene.physics.add.sprite(x, y, "");
        physicsBody.setCircle(20);
        physicsBody.setCollideWorldBounds(true); 

        this.body = physicsBody.body as Phaser.Physics.Arcade.Body;

        this.container = this.scene.add.container(x, y, [this.graphics]);
        this.scene.physics.world.enable(this.container);
    }

    
    private drawBlob(x: number, y: number, color: number) {
        this.graphics.clear();
        this.graphics.fillStyle(color, 1);
        this.graphics.fillCircle(x, y, 20);
    }

    move(dx: number, dy: number, delta: number) {
        const speedFactor = delta / 1000; // Convert delta time to seconds
        this.body.setVelocity(dx * this.baseSpeed, dy * this.baseSpeed);

        // Sync the graphics position with the physics body
        this.container.x = this.body.position.x;
        this.container.y = this.body.position.y;
    }

    getPosition() {
        return { x: this.container.x, y: this.container.y };
    }
}
