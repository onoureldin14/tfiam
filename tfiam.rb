class Tfiam < Formula
  desc "TFIAM - Analyze Terraform repositories and generate IAM permission recommendations with AI explanations"
  homepage "https://github.com/onoureldin14/tfiam"
  url "https://github.com/onoureldin14/tfiam/archive/refs/heads/main.zip"
  version "1.0.0"
  sha256 ""  # This will be calculated automatically when you push to GitHub
  license "MIT"

  depends_on "python@3.11"

  def install
    # Create virtual environment
    venv = virtualenv_create(libexec, "python3.11")

    # Install Python dependencies from requirements.txt
    venv.pip_install "openai>=1.0.0"
    venv.pip_install "pbr>=1.7.5"

    # Install the TFIAM package
    venv.pip_install_and_link buildpath

    # Create a wrapper script that calls the main.py
    (bin/"tfiam").write <<~EOS
      #!/bin/bash
      exec "#{libexec}/bin/python" "#{libexec}/lib/python3.11/site-packages/main.py" "$@"
    EOS

    chmod 0755, bin/"tfiam"
  end

  test do
    system "#{bin}/tfiam", "--help"
  end
end
