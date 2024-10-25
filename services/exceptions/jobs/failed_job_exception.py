
class FailedJobException(Exception):
  def __init__(self, message: str, error_code: int = 0):
    super().__init__(message)
    self.error_code = error_code
    self.reason = message

  def __str__(self):
    detalles: str = f"Error Job Failed - code: {self.error_code} - {self.reason}"
    detalles += f"\n\n{self.args[0]}"
    return detalles 
