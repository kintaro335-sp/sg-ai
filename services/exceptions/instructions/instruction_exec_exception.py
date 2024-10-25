

class InstructionError(Exception):
  def __init__(self, message: str):
    super().__init__(message)
    self.reason = message

  def __str__(self):
    detalles: str = f"Error executing instruction - code: - {self.reason}"
    detalles += f"\n\n{self.args[0]}"
    return detalles 

