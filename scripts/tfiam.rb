class Tfiam < Formula
  desc "TFIAM - Analyze Terraform repositories and generate IAM permission recommendations with AI explanations"
  homepage "https://github.com/yourusername/tfiam"
  url "https://github.com/yourusername/tfiam/archive/v1.0.0.tar.gz"
  sha256 "your_sha256_here"
  license "MIT"

  depends_on "python@3.11"

  def install
    # Create a virtual environment
    venv = virtualenv_create(libexec, "python3.11")

    # Install dependencies from requirements.txt
    libexec.install "requirements.txt"
    system libexec/"bin/pip", "install", "-r", libexec/"requirements.txt"

    # Copy the main script
    libexec.install "main.py"

    # Create a wrapper script
    (bin/"tfiam").write <<~EOS
      #!/bin/bash
      exec "#{libexec}/bin/python" "#{libexec}/main.py" "$@"
    EOS

    # Make the wrapper executable
    chmod 0755, bin/"tfiam"
  end

  test do
    # Test that the tool runs without errors
    system "#{bin}/tfiam", "--help"
  end
end
