import Phaser from "phaser";
import axios from "axios";

export class Home extends Phaser.Scene {
  private nameInput!: HTMLInputElement;
  private colorInput!: HTMLInputElement;
  private playButton!: HTMLButtonElement;

  constructor() {
    super("Home");
  }

  create() {
    this.createUI();
    this.scale.on("resize", this.resizeUI, this);
  }

  createUI() {
    const container = document.createElement("div");
    container.id = "ui-container";
    this.applyContainerStyle(container);
    document.body.appendChild(container);
    (this as any).uiContainer = container;

    // Logo
    const logo = document.createElement("img");
    logo.src = "/agarish.png"; // Better path for static assets
    logo.alt = "Agar.ish Logo";
    logo.style.width = "700px";
    logo.style.marginBottom = "20px";
    container.appendChild(logo);

    // Name input
    this.nameInput = document.createElement("input");
    this.nameInput.placeholder = "Enter your name";
    this.styleNameInput(this.nameInput);
    container.appendChild(this.nameInput);

    // Color label + input wrapper
    const colorWrapper = document.createElement("div");
    colorWrapper.style.display = "flex";
    colorWrapper.style.alignItems = "center";
    colorWrapper.style.gap = "10px";

    const colorLabel = document.createElement("label");
    colorLabel.innerText = "Choose Color:";
    this.styleColorLabel(colorLabel);
    colorWrapper.appendChild(colorLabel);

    this.colorInput = document.createElement("input");
    this.colorInput.type = "color";
    this.colorInput.value = "#00ff00";
    this.styleColorInput(this.colorInput);
    colorWrapper.appendChild(this.colorInput);

    container.appendChild(colorWrapper);

    // Play button
    this.playButton = document.createElement("button");
    this.playButton.innerText = "Play";
    this.stylePlayButton(this.playButton);
    container.appendChild(this.playButton);

    // Play click event
    this.playButton.addEventListener("click", async () => {
      const playerName = this.nameInput.value || "Player";
      const playerColor = "0x" + this.colorInput.value.slice(1);

      try {
        const response = await axios.post("http://127.0.0.1:8000/game/create_player/", {
          name: playerName,
          color: playerColor,
        });

        console.log("Player Created:", response.data);
        document.body.removeChild(container);

        const playerID = response.data.player_id;
        this.scene.start("Game", { playerID });
      } catch (error) {
        console.error("Error sending player data:", error);
        alert("Failed to start the game.");
      }
    });

    this.resizeUI(this.scale.gameSize);
  }

  private resizeUI(gameSize: Phaser.Structs.Size) {
    const container = (this as any).uiContainer as HTMLDivElement;
    if (container) {
      container.style.width = `${gameSize.width}px`;
      container.style.height = `${gameSize.height}px`;
    }
  }

  private applyContainerStyle(container: HTMLDivElement) {
    Object.assign(container.style, {
      position: "absolute",
      top: "0",
      left: "0",
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      gap: "20px",
      backgroundColor: "transparent",
      zIndex: "1000",
      pointerEvents: "auto",
    });
  }

  // Style functions for each element
  private styleNameInput(element: HTMLInputElement) {
    Object.assign(element.style, {
      fontSize: "18px",
      padding: "10px",
      borderRadius: "8px",
      border: "1px solid #aaa",
      width: "220px",
      textAlign: "center",
      boxShadow: "0 2px 4px rgba(0,0,0,0.1)",
    });
  }

  private styleColorInput(element: HTMLInputElement) {
    Object.assign(element.style, {
      width: "30px",
      height: "30px",
      border: "none",
      cursor: "pointer",
      background: "rgba(255, 255, 255, 0)"
    });
  }

  private styleColorLabel(label: HTMLLabelElement) {
    Object.assign(label.style, {
      fontSize: "18px",
      color: "rgb(78, 78, 78)",
      fontFamily: "Arial",
      flex: "1",
      textAlign: "left",
    });
  }

  private stylePlayButton(element: HTMLButtonElement) {
    Object.assign(element.style, {
      fontSize: "18px",
      padding: "10px 20px",
      borderRadius: "8px",
      border: "none",
      backgroundColor: "rgb(143, 210, 127)",
      color: "#fff",
      cursor: "pointer",
      boxShadow: "0 2px 4px rgba(0,0,0,0.5)",
      width: "220px",

    });

    element.onmouseenter = () => element.style.backgroundColor = "#45a049";
    element.onmouseleave = () => element.style.backgroundColor = "#4CAF50";
  }
}
