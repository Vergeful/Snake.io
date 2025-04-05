import Phaser from "phaser";
import axios from "axios";

export class Home extends Phaser.Scene {
  private nameInput!: HTMLInputElement;
  private colorSelect!: HTMLSelectElement;
  private playButton!: HTMLButtonElement;
  private selectedColor: number = 0x00ff00; // Default color

  constructor() {
    super("Home");
  }

  create() {
    this.createUI();

    this.scale.on("resize", this.resizeUI, this);
  }

  createUI() {
    // Get center coordinates dynamically
    const { width, height } = this.scale;

    // Name Input (HTML)
    this.nameInput = document.createElement("input");
    this.nameInput.type = "text";
    this.nameInput.placeholder = "Enter your name...";
    this.styleHTMLElement(this.nameInput, width / 2, height * 0.35);
    document.body.appendChild(this.nameInput);

    // Color Selection Text
    this.add.text(width / 2, height * 0.45, "Select Your Color:", {
      fontSize: "18px",
      color: "#000000",
    }).setOrigin(0.5);

    // Color Dropdown (HTML)
    this.colorSelect = document.createElement("select");
    this.styleHTMLElement(this.colorSelect, width / 2, height * 0.5);
    document.body.appendChild(this.colorSelect);

    const colors = [
      { name: "Green", value: "0x00ff00" },
      { name: "Red", value: "0xff0000" },
      { name: "Blue", value: "0x0000ff" },
      { name: "Yellow", value: "0xffff00" },
      { name: "Pink", value: "0xff00ff" },
    ];

    colors.forEach((color) => {
      const option = document.createElement("option");
      option.value = color.value;
      option.innerText = color.name;
      this.colorSelect.appendChild(option);
    });

    // Play Button (HTML)
    this.playButton = document.createElement("button");
    this.playButton.innerText = "Play";
    this.styleHTMLElement(this.playButton, width / 2, height * 0.6);
    document.body.appendChild(this.playButton);

    this.playButton.addEventListener("click", async () => {
      const playerName = this.nameInput.value || "Player";
      const playerColor = this.colorSelect.value;
  
      try {
          const response = await axios.post("http://localhost:8000/proxy/create_player/", {
              name: playerName,
              color: playerColor,
          });
  
          console.log("Player Created:", response.data);
  
          // Cleanup UI elements
          document.body.removeChild(this.nameInput);
          document.body.removeChild(this.colorSelect);
          document.body.removeChild(this.playButton);

          const playerID = response.data.player_id;
  
          // Start game
          this.scene.start("Game", { playerName, playerColor, playerID });
  
      } catch (error) {
          console.error("Error sending player data:", error);
          alert("Failed to start the game.");
      }
  });
  }

  // Function to style HTML elements and position them
  private styleHTMLElement(element: HTMLElement, x: number, y: number) {
    element.style.position = "absolute";
    element.style.left = `${x - 75}px`; 
    element.style.top = `${y}px`;
    element.style.width = "150px";
    element.style.textAlign = "center";
    element.style.fontSize = "18px";
    element.style.padding = "5px";
  }

  // Resize UI when the window is resized
  private resizeUI(gameSize: Phaser.Structs.Size) {
    const { width, height } = gameSize;

    // Update HTML element positions
    this.styleHTMLElement(this.nameInput, width / 2, height * 0.35);
    this.styleHTMLElement(this.colorSelect, width / 2, height * 0.5);
    this.styleHTMLElement(this.playButton, width / 2, height * 0.6);
  }
}
