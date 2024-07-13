import torch
import torch.optim as optim
from tqdm import tqdm
import numpy as np
from lossFunction import bce_dice_loss
from evaluate import evaluate_model

def train_model(model, train_dataset, validation_dataset, epochs=10, device='cuda'):
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)
    model.to(device)  # Move model to GPU if available
    batch_losses = []
    val_losses = []
    best_IoU = 0.0
    
    for epoch in range(epochs):
        model.train()
        losses = []
        print(f'Epoch {epoch+1}/{epochs}')
        progress = tqdm(train_dataset)
        
        for tf_inputs, tf_labels in progress:
            inputs = torch.from_numpy(tf_inputs.numpy()).permute(0, 3, 1, 2).float().to(device)  # Convert to PyTorch tensors and move to GPU
            labels = torch.from_numpy(tf_labels.numpy()).permute(0, 3, 1, 2).float().to(device)  # Move to GPU

            optimizer.zero_grad()
            outputs = model(inputs)
            
            # Convert outputs and labels to TensorFlow tensors for loss computation
            outputs_tf = tf.convert_to_tensor(outputs.detach().cpu().numpy())
            labels_tf = tf.convert_to_tensor(labels.detach().cpu().numpy())
            
            loss = bce_dice_loss(labels_tf, outputs_tf)
            loss = torch.tensor(loss.numpy()).to(device)  # Convert back to PyTorch tensor and move to GPU
            
            loss.backward()
            optimizer.step()

            losses.append(loss.item())
            progress.set_postfix({'batch_loss': loss.item()})
        
        print("Evaluation...")
        model.eval()
        IoU, recall, precision, val_loss = evaluate_model(lambda x: torch.sigmoid(model(x)).detach().cpu().numpy(), validation_dataset)
        print(f"Mean IoU: {IoU}\nMean precision: {precision}\nMean recall: {recall}\nValidation loss: {val_loss}\n")
        
        if IoU > best_IoU:
            best_IoU = IoU
            torch.save(model.state_dict(), "best_vit_model.pth")
        
        print(f'Epoch: {epoch}, Train loss: {np.mean(losses)}')
        batch_losses.append(np.mean(losses))
        val_losses.append(val_loss)
    
    print(f"Best model IoU: {best_IoU}")
    return batch_losses, val_losses
